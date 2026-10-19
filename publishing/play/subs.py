"""Google Play subscription management (monetization.subscriptions v3).

This module wraps the monetization.subscriptions resource of the Android
Publisher API v3 to create, list, get, patch, and archive auto renewing
subscriptions for a Google Play application. It also covers base plans
and offers, which are the two sub resources that describe billing cadence
and promotional pricing respectively.

API reference
    Base URL: https://androidpublisher.googleapis.com/androidpublisher/v3/
    Docs:     https://developers.google.com/android-publisher/api-ref/rest/v3/monetization.subscriptions
    Scope:    https://www.googleapis.com/auth/androidpublisher

Resource model
    Subscription has: productId (SKU), basePlans (array of base plans),
        listings (localized title and description), taxAndComplianceSettings.
    BasePlan has: basePlanId, state, regionalConfigs (per region price),
        offers (array of promotional offers), autoRenewingBasePlanType
        (with billingPeriodDuration in ISO 8601) or prepaidBasePlanType.
    Offer has: offerId, phases (array of pricing phases; e.g. free trial
        followed by paid introductory pricing), targeting rules.

Billing period examples (ISO 8601 durations)
    P1W = weekly, P1M = monthly, P3M = quarterly, P6M = semi annual,
    P1Y = yearly.

Pricing
    Prices are expressed in micros (1 USD = 1000000 micros) and are
    keyed by ISO 3166 region code in regionalConfigs.

External dependencies
    pip install google-api-python-client google-auth
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    from publishing.play.client import (
        PlayAPIError,
        PlayAuthError,
        PlayClient,
        PlayValidationError,
        get_default_client,
    )
    _CLIENT_AVAILABLE = True
    _CLIENT_IMPORT_ERROR = ""
except ImportError as _exc:
    PlayAPIError = Exception  # type: ignore
    PlayAuthError = Exception  # type: ignore
    PlayClient = object  # type: ignore
    PlayValidationError = Exception  # type: ignore
    get_default_client = None  # type: ignore
    _CLIENT_AVAILABLE = False
    _CLIENT_IMPORT_ERROR = (
        "publishing.play.client is unavailable. Ensure the module is on the "
        "PYTHONPATH and Google API client libraries are installed. "
        "Original error: {0}".format(_exc)
    )


_LOG = logging.getLogger("publishing.play.subs")
if not _LOG.handlers:
    _LOG.addHandler(logging.NullHandler())


STATE_DRAFT = "draft"
STATE_ACTIVE = "active"
STATE_INACTIVE = "inactive"

VALID_STATES: set[str] = {STATE_DRAFT, STATE_ACTIVE, STATE_INACTIVE}

RECURRENCE_FINITE = "FINITE_RECURRING"
RECURRENCE_INFINITE = "INFINITE_RECURRING"
RECURRENCE_NON_RECURRING = "NON_RECURRING"

VALID_RECURRENCE_MODES: set[str] = {
    RECURRENCE_FINITE,
    RECURRENCE_INFINITE,
    RECURRENCE_NON_RECURRING,
}

PRODUCT_ID_PATTERN = re.compile(r"^[a-z0-9_.]{1,40}$")
PRODUCT_ID_MAX_LENGTH = 40

BASE_PLAN_ID_PATTERN = re.compile(r"^[a-z0-9-]{1,63}$")
OFFER_ID_PATTERN = re.compile(r"^[a-z0-9-]{1,63}$")

BILLING_PERIOD_PATTERN = re.compile(r"^P(\d+)(D|W|M|Y)$")

DEFAULT_CURRENCY = "USD"
DEFAULT_REGION = "US"
DEFAULT_LANGUAGE = "en-US"
DEFAULT_BILLING_PERIOD_MONTHLY = "P1M"
DEFAULT_BILLING_PERIOD_YEARLY = "P1Y"


def validate_product_id(product_id: str) -> tuple[bool, str]:
    """Validate a subscription productId identifier."""
    if product_id is None or not isinstance(product_id, str):
        return False, "product_id must be a string"
    if not product_id:
        return False, "product_id is empty"
    if len(product_id) > PRODUCT_ID_MAX_LENGTH:
        return False, "product_id exceeds {0} characters (got {1})".format(
            PRODUCT_ID_MAX_LENGTH, len(product_id)
        )
    if not PRODUCT_ID_PATTERN.match(product_id):
        return False, (
            "product_id must match ^[a-z0-9_.]{1,40}$; only lowercase "
            "letters, digits, underscores, and dots are allowed"
        )
    return True, "ok"


def validate_base_plan_id(base_plan_id: str) -> tuple[bool, str]:
    """Validate a basePlanId identifier."""
    if not isinstance(base_plan_id, str) or not base_plan_id:
        return False, "base_plan_id must be a non empty string"
    if not BASE_PLAN_ID_PATTERN.match(base_plan_id):
        return False, (
            "base_plan_id must match ^[a-z0-9-]{1,63}$"
        )
    return True, "ok"


def validate_offer_id(offer_id: str) -> tuple[bool, str]:
    """Validate an offerId identifier."""
    if not isinstance(offer_id, str) or not offer_id:
        return False, "offer_id must be a non empty string"
    if not OFFER_ID_PATTERN.match(offer_id):
        return False, (
            "offer_id must match ^[a-z0-9-]{1,63}$"
        )
    return True, "ok"


def validate_billing_period(duration: str) -> tuple[bool, str]:
    """Validate an ISO 8601 billing period duration."""
    if not isinstance(duration, str) or not duration:
        return False, "billing_period must be a non empty string"
    if not BILLING_PERIOD_PATTERN.match(duration):
        return False, (
            "billing_period must match ^P\\d+(D|W|M|Y)$ (e.g. P1M or P1Y)"
        )
    return True, "ok"


def _validate_price_micros(price_micros: Any) -> int:
    """Coerce and validate a price in micros."""
    try:
        price_int = int(price_micros)
    except (TypeError, ValueError) as exc:
        raise PlayValidationError(
            "price_micros must be an integer, got {0}".format(price_micros)
        ) from exc
    if price_int < 0:
        raise PlayValidationError(
            "price_micros must be non negative (got {0})".format(price_int)
        )
    return price_int


def _validate_currency(currency: str) -> str:
    """Validate an ISO 4217 currency code."""
    if not isinstance(currency, str) or not currency:
        raise PlayValidationError("currency must be a non empty string")
    code = currency.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise PlayValidationError(
            "currency must be a 3 letter ISO 4217 code, got {0}".format(currency)
        )
    return code


@dataclass
class PricingPhase:
    """A single pricing phase inside a subscription offer.

    Attributes:
        duration: ISO 8601 duration for the phase (e.g. P7D for a 7 day
            free trial, or P1M for one monthly billing cycle).
        recurrence_mode: One of FINITE_RECURRING, INFINITE_RECURRING, or
            NON_RECURRING.
        billing_cycle_count: Required for FINITE_RECURRING. Number of
            repeats at this phase before moving on.
        regional_configs: List of per region price overrides. Each item
            is a dict of shape {regionCode, price: {currencyCode, units,
            nanos}} or a simplified {region, price_micros, currency}
            mapping which will be expanded.
    """

    duration: str
    recurrence_mode: str = RECURRENCE_INFINITE
    billing_cycle_count: int = 0
    regional_configs: list[dict[str, Any]] = field(default_factory=list)

    def to_api(self) -> dict[str, Any]:
        """Return the API shape for this phase."""
        ok, message = validate_billing_period(self.duration)
        if not ok:
            raise PlayValidationError(
                "PricingPhase duration invalid: {0}".format(message)
            )
        if self.recurrence_mode not in VALID_RECURRENCE_MODES:
            raise PlayValidationError(
                "recurrence_mode {0} must be one of {1}".format(
                    self.recurrence_mode, sorted(VALID_RECURRENCE_MODES)
                )
            )
        body: dict[str, Any] = {
            "duration": self.duration,
            "recurrenceMode": self.recurrence_mode,
        }
        if self.recurrence_mode == RECURRENCE_FINITE:
            if int(self.billing_cycle_count) <= 0:
                raise PlayValidationError(
                    "billing_cycle_count must be > 0 for FINITE_RECURRING"
                )
            body["billingCycleCount"] = int(self.billing_cycle_count)
        body["regionalConfigs"] = _normalise_regional_configs(
            self.regional_configs
        )
        return body


@dataclass
class BasePlanConfig:
    """Auto renewing base plan configuration."""

    base_plan_id: str
    billing_period: str = DEFAULT_BILLING_PERIOD_MONTHLY
    price_micros: int = 499_000
    currency: str = DEFAULT_CURRENCY
    auto_renewing: bool = True
    region: str = DEFAULT_REGION

    def to_api(self) -> dict[str, Any]:
        """Return the API body for this base plan."""
        ok, message = validate_base_plan_id(self.base_plan_id)
        if not ok:
            raise PlayValidationError(
                "BasePlanConfig base_plan_id invalid: {0}".format(message)
            )
        ok, message = validate_billing_period(self.billing_period)
        if not ok:
            raise PlayValidationError(
                "BasePlanConfig billing_period invalid: {0}".format(message)
            )
        price_int = _validate_price_micros(self.price_micros)
        currency_code = _validate_currency(self.currency)
        body: dict[str, Any] = {
            "basePlanId": self.base_plan_id,
            "state": STATE_DRAFT,
            "regionalConfigs": [
                {
                    "regionCode": self.region.upper(),
                    "price": {
                        "currencyCode": currency_code,
                        "units": str(price_int // 1_000_000),
                        "nanos": int((price_int % 1_000_000) * 1000),
                    },
                }
            ],
        }
        if self.auto_renewing:
            body["autoRenewingBasePlanType"] = {
                "billingPeriodDuration": self.billing_period,
                "gracePeriodDuration": "P7D",
                "resubscribeState": "RESUBSCRIBE_STATE_ACTIVE",
                "prorationMode": (
                    "SUBSCRIPTION_PRORATION_MODE_CHARGE_ON_NEXT_BILLING_DATE"
                ),
            }
        else:
            body["prepaidBasePlanType"] = {
                "billingPeriodDuration": self.billing_period,
                "timeExtension": "TIME_EXTENSION_ACTIVE",
            }
        return body


@dataclass
class OfferConfig:
    """Promotional offer configuration (e.g. free trial plus intro)."""

    offer_id: str
    phases: list[PricingPhase] = field(default_factory=list)
    eligibility_rules: Optional[dict[str, Any]] = None

    def to_api(self) -> dict[str, Any]:
        """Return the API body for this offer."""
        ok, message = validate_offer_id(self.offer_id)
        if not ok:
            raise PlayValidationError(
                "OfferConfig offer_id invalid: {0}".format(message)
            )
        if not self.phases:
            raise PlayValidationError("OfferConfig must have at least one phase")
        body: dict[str, Any] = {
            "offerId": self.offer_id,
            "state": STATE_DRAFT,
            "phases": [phase.to_api() for phase in self.phases],
        }
        if self.eligibility_rules is not None:
            body["targeting"] = dict(self.eligibility_rules)
        return body


def _normalise_regional_configs(
    configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalise a list of regional configs to the API shape."""
    out: list[dict[str, Any]] = []
    if not isinstance(configs, list):
        return out
    for entry in configs:
        if not isinstance(entry, dict):
            continue
        if "price" in entry and "regionCode" in entry:
            out.append(dict(entry))
            continue
        region = str(entry.get("region") or entry.get("regionCode") or DEFAULT_REGION)
        price_micros = int(entry.get("price_micros") or entry.get("priceMicros") or 0)
        currency = str(
            entry.get("currency") or entry.get("currencyCode") or DEFAULT_CURRENCY
        ).upper()
        out.append(
            {
                "regionCode": region.upper(),
                "price": {
                    "currencyCode": currency,
                    "units": str(price_micros // 1_000_000),
                    "nanos": int((price_micros % 1_000_000) * 1000),
                },
            }
        )
    if not out:
        out.append(
            {
                "regionCode": DEFAULT_REGION,
                "price": {
                    "currencyCode": DEFAULT_CURRENCY,
                    "units": "0",
                    "nanos": 0,
                },
            }
        )
    return out


def _listings_body(
    title: str,
    description: str,
    language: str = DEFAULT_LANGUAGE,
) -> list[dict[str, Any]]:
    """Return the localized listings array for a subscription."""
    if not title:
        raise PlayValidationError("subscription title is required")
    if not description:
        raise PlayValidationError("subscription description is required")
    return [
        {
            "languageCode": language,
            "title": title,
            "description": description,
        }
    ]


class SubscriptionManager:
    """Manage auto renewing subscriptions for a Play application."""

    def __init__(self, client: Optional[Any] = None) -> None:
        """Initialise the manager.

        Args:
            client: Authenticated PlayClient. When None, a default client
                is loaded from environment variables via get_default_client.
        """
        if client is not None:
            self.client = client
        else:
            if not _CLIENT_AVAILABLE or get_default_client is None:
                raise PlayAuthError(_CLIENT_IMPORT_ERROR)
            self.client = get_default_client()

    def _package(self, override: Optional[str] = None) -> str:
        """Return the package name, preferring an explicit override."""
        if override:
            return override
        package = getattr(self.client, "app_package_name", None)
        if not package:
            raise PlayAuthError(
                "Application package name is not configured on PlayClient."
            )
        return package

    def _subscriptions_resource(self) -> Any:
        """Return the monetization.subscriptions resource on the client."""
        service = getattr(self.client, "service", None)
        if service is None:
            raise PlayAuthError(
                "PlayClient service is unavailable; authenticate first."
            )
        monetization = service.monetization()
        return monetization.subscriptions()

    def list_subscriptions(self, package_name: str) -> list[dict]:
        """List all subscriptions for a package, paginating as needed."""
        package = self._package(package_name)
        out: list[dict] = []
        token: Optional[str] = None
        while True:
            kwargs: dict[str, Any] = {"packageName": package}
            if token:
                kwargs["pageToken"] = token
            request = self._subscriptions_resource().list(**kwargs)
            result = self.client.execute(
                request, operation="monetization.subscriptions.list"
            )
            if not isinstance(result, dict):
                break
            items = result.get("subscriptions") or []
            if isinstance(items, list):
                out.extend(items)
            next_token = result.get("nextPageToken")
            if not next_token:
                break
            token = next_token
        _LOG.info(
            "monetization.subscriptions.list package=%s count=%d",
            package,
            len(out),
        )
        return out

    def get_subscription(self, package_name: str, product_id: str) -> dict:
        """Return a single subscription resource."""
        ok, message = validate_product_id(product_id)
        if not ok:
            raise PlayValidationError(
                "invalid product_id {0}: {1}".format(product_id, message)
            )
        package = self._package(package_name)
        request = self._subscriptions_resource().get(
            packageName=package,
            productId=product_id,
        )
        return self.client.execute(
            request, operation="monetization.subscriptions.get"
        )

    def create_subscription(
        self,
        package_name: str,
        product_id: str,
        title: str,
        description: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> dict:
        """Create a subscription product with a single localized listing."""
        ok, message = validate_product_id(product_id)
        if not ok:
            raise PlayValidationError(
                "invalid product_id {0}: {1}".format(product_id, message)
            )
        package = self._package(package_name)
        body: dict[str, Any] = {
            "packageName": package,
            "productId": product_id,
            "basePlans": [],
            "listings": _listings_body(title, description, language),
            "taxAndComplianceSettings": {
                "eeaWithdrawalRightType": (
                    "WITHDRAWAL_RIGHT_SERVICE"
                ),
                "isTokenizedDigitalAsset": False,
            },
        }
        request = self._subscriptions_resource().create(
            packageName=package,
            productId=product_id,
            body=body,
        )
        result = self.client.execute(
            request, operation="monetization.subscriptions.create"
        )
        _LOG.info(
            "monetization.subscriptions.create package=%s product_id=%s",
            package,
            product_id,
        )
        return result

    def patch_subscription(
        self,
        package_name: str,
        product_id: str,
        updates: dict,
        update_mask: list[str],
    ) -> dict:
        """Patch a subscription using a field mask."""
        ok, message = validate_product_id(product_id)
        if not ok:
            raise PlayValidationError(
                "invalid product_id {0}: {1}".format(product_id, message)
            )
        if not isinstance(updates, dict) or not updates:
            raise PlayValidationError("updates must be a non empty dict")
        if not isinstance(update_mask, list) or not update_mask:
            raise PlayValidationError("update_mask must be a non empty list")
        package = self._package(package_name)
        body = dict(updates)
        body["packageName"] = package
        body["productId"] = product_id
        request = self._subscriptions_resource().patch(
            packageName=package,
            productId=product_id,
            updateMask=",".join(update_mask),
            body=body,
        )
        result = self.client.execute(
            request, operation="monetization.subscriptions.patch"
        )
        _LOG.info(
            "monetization.subscriptions.patch product_id=%s fields=%s",
            product_id,
            list(update_mask),
        )
        return result

    def archive_subscription(
        self,
        package_name: str,
        product_id: str,
    ) -> dict:
        """Archive a subscription so it cannot be purchased again."""
        ok, message = validate_product_id(product_id)
        if not ok:
            raise PlayValidationError(
                "invalid product_id {0}: {1}".format(product_id, message)
            )
        package = self._package(package_name)
        request = self._subscriptions_resource().archive(
            packageName=package,
            productId=product_id,
        )
        result = self.client.execute(
            request, operation="monetization.subscriptions.archive"
        )
        _LOG.info(
            "monetization.subscriptions.archive product_id=%s",
            product_id,
        )
        return result

    def add_base_plan(
        self,
        package_name: str,
        product_id: str,
        base_plan_id: str,
        auto_renewing: bool = True,
        billing_period: str = DEFAULT_BILLING_PERIOD_MONTHLY,
        price_micros: int = 499_000,
        currency: str = DEFAULT_CURRENCY,
    ) -> dict:
        """Append a base plan to an existing subscription via patch."""
        ok, message = validate_base_plan_id(base_plan_id)
        if not ok:
            raise PlayValidationError(
                "invalid base_plan_id {0}: {1}".format(base_plan_id, message)
            )
        ok, message = validate_billing_period(billing_period)
        if not ok:
            raise PlayValidationError(
                "invalid billing_period {0}: {1}".format(billing_period, message)
            )
        package = self._package(package_name)
        current = self.get_subscription(package, product_id)
        plans: list[dict[str, Any]] = []
        if isinstance(current, dict):
            existing = current.get("basePlans")
            if isinstance(existing, list):
                plans.extend(existing)
        plan_body = BasePlanConfig(
            base_plan_id=base_plan_id,
            billing_period=billing_period,
            price_micros=int(price_micros),
            currency=currency,
            auto_renewing=bool(auto_renewing),
        ).to_api()
        plans = [p for p in plans if p.get("basePlanId") != base_plan_id]
        plans.append(plan_body)
        return self.patch_subscription(
            package_name=package,
            product_id=product_id,
            updates={"basePlans": plans},
            update_mask=["basePlans"],
        )

    def add_offer(
        self,
        package_name: str,
        product_id: str,
        base_plan_id: str,
        offer_id: str,
        phases: list[dict],
    ) -> dict:
        """Append an offer to a base plan via patch.

        Each entry in phases may either be a PricingPhase (serialised
        via to_api) or a raw dict matching the API shape.
        """
        ok, message = validate_base_plan_id(base_plan_id)
        if not ok:
            raise PlayValidationError(
                "invalid base_plan_id {0}: {1}".format(base_plan_id, message)
            )
        ok, message = validate_offer_id(offer_id)
        if not ok:
            raise PlayValidationError(
                "invalid offer_id {0}: {1}".format(offer_id, message)
            )
        if not isinstance(phases, list) or not phases:
            raise PlayValidationError("phases must be a non empty list")
        package = self._package(package_name)
        current = self.get_subscription(package, product_id)
        plans: list[dict[str, Any]] = []
        if isinstance(current, dict):
            existing = current.get("basePlans")
            if isinstance(existing, list):
                plans.extend(existing)
        target: Optional[dict[str, Any]] = None
        for plan in plans:
            if plan.get("basePlanId") == base_plan_id:
                target = plan
                break
        if target is None:
            raise PlayValidationError(
                "base_plan_id {0} not found on subscription {1}".format(
                    base_plan_id, product_id
                )
            )
        phase_bodies: list[dict[str, Any]] = []
        for entry in phases:
            if isinstance(entry, PricingPhase):
                phase_bodies.append(entry.to_api())
            elif isinstance(entry, dict):
                phase_bodies.append(entry)
            else:
                raise PlayValidationError(
                    "phase entry must be PricingPhase or dict"
                )
        offers = target.get("offers")
        if not isinstance(offers, list):
            offers = []
        offers = [o for o in offers if o.get("offerId") != offer_id]
        offers.append(
            {
                "offerId": offer_id,
                "state": STATE_DRAFT,
                "phases": phase_bodies,
            }
        )
        target["offers"] = offers
        return self.patch_subscription(
            package_name=package,
            product_id=product_id,
            updates={"basePlans": plans},
            update_mask=["basePlans"],
        )

    def activate_base_plan(
        self,
        package_name: str,
        product_id: str,
        base_plan_id: str,
    ) -> dict:
        """Activate a base plan so users can subscribe to it."""
        ok, message = validate_base_plan_id(base_plan_id)
        if not ok:
            raise PlayValidationError(
                "invalid base_plan_id {0}: {1}".format(base_plan_id, message)
            )
        package = self._package(package_name)
        resource = self._subscriptions_resource()
        try:
            base_plans = resource.basePlans()
        except AttributeError as exc:
            raise PlayAPIError(
                "basePlans sub resource unavailable on monetization.subscriptions"
            ) from exc
        request = base_plans.activate(
            packageName=package,
            productId=product_id,
            basePlanId=base_plan_id,
            body={},
        )
        result = self.client.execute(
            request, operation="monetization.subscriptions.basePlans.activate"
        )
        _LOG.info(
            "base_plan.activate product_id=%s base_plan_id=%s",
            product_id,
            base_plan_id,
        )
        return result


def standard_subscriptions() -> list[dict]:
    """Return a sample set of monthly, yearly, and free trial subs."""
    monthly = {
        "product_id": "sub_pro_monthly",
        "title": "Pro Monthly",
        "description": "Full access to all pro features, billed monthly.",
        "base_plans": [
            BasePlanConfig(
                base_plan_id="monthly-autorenew",
                billing_period=DEFAULT_BILLING_PERIOD_MONTHLY,
                price_micros=4_990_000,
                currency="USD",
                auto_renewing=True,
            ).to_api()
        ],
    }
    yearly = {
        "product_id": "sub_pro_yearly",
        "title": "Pro Yearly",
        "description": "Full access to all pro features, billed yearly.",
        "base_plans": [
            BasePlanConfig(
                base_plan_id="yearly-autorenew",
                billing_period=DEFAULT_BILLING_PERIOD_YEARLY,
                price_micros=39_990_000,
                currency="USD",
                auto_renewing=True,
            ).to_api()
        ],
    }
    trial_phase = PricingPhase(
        duration="P7D",
        recurrence_mode=RECURRENCE_FINITE,
        billing_cycle_count=1,
        regional_configs=[
            {"region": "US", "price_micros": 0, "currency": "USD"}
        ],
    )
    paid_phase = PricingPhase(
        duration=DEFAULT_BILLING_PERIOD_MONTHLY,
        recurrence_mode=RECURRENCE_INFINITE,
        regional_configs=[
            {"region": "US", "price_micros": 4_990_000, "currency": "USD"}
        ],
    )
    with_trial = {
        "product_id": "sub_pro_trial",
        "title": "Pro with Free Trial",
        "description": "Seven day free trial, then monthly billing.",
        "base_plans": [
            BasePlanConfig(
                base_plan_id="monthly-autorenew",
                billing_period=DEFAULT_BILLING_PERIOD_MONTHLY,
                price_micros=4_990_000,
                currency="USD",
                auto_renewing=True,
            ).to_api()
        ],
        "offers": [
            OfferConfig(
                offer_id="intro-7d-free",
                phases=[trial_phase, paid_phase],
            ).to_api()
        ],
    }
    return [monthly, yearly, with_trial]


def _main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for subscription management."""
    parser = argparse.ArgumentParser(
        prog="publishing.play.subs",
        description="Manage Google Play auto renewing subscriptions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_cmd = subparsers.add_parser(
        "validate", help="Validate a productId identifier."
    )
    validate_cmd.add_argument("--product-id", required=True)
    validate_cmd.set_defaults(handler="validate")

    sample_cmd = subparsers.add_parser(
        "sample", help="Print the sample subscription set as JSON."
    )
    sample_cmd.set_defaults(handler="sample")

    list_cmd = subparsers.add_parser(
        "list", help="List subscriptions for the configured package."
    )
    list_cmd.add_argument("--package", required=False, default=None)
    list_cmd.set_defaults(handler="list")

    get_cmd = subparsers.add_parser(
        "get", help="Get a subscription by productId."
    )
    get_cmd.add_argument("--package", required=False, default=None)
    get_cmd.add_argument("--product-id", required=True)
    get_cmd.set_defaults(handler="get")

    args = parser.parse_args(argv)

    if args.handler == "validate":
        ok, message = validate_product_id(args.product_id)
        print(json.dumps({"ok": ok, "message": message}, indent=2))
        return 0 if ok else 1
    if args.handler == "sample":
        print(json.dumps(standard_subscriptions(), indent=2))
        return 0
    if args.handler == "list":
        manager = SubscriptionManager()
        package = args.package or manager.client.app_package_name
        items = manager.list_subscriptions(package)
        print(json.dumps({"count": len(items)}, indent=2))
        return 0
    if args.handler == "get":
        manager = SubscriptionManager()
        package = args.package or manager.client.app_package_name
        sub = manager.get_subscription(package, args.product_id)
        print(json.dumps(sub, indent=2, default=str))
        return 0
    parser.error("unknown command")
    return 2


__all__ = [
    "BASE_PLAN_ID_PATTERN",
    "BILLING_PERIOD_PATTERN",
    "BasePlanConfig",
    "DEFAULT_BILLING_PERIOD_MONTHLY",
    "DEFAULT_BILLING_PERIOD_YEARLY",
    "DEFAULT_CURRENCY",
    "DEFAULT_LANGUAGE",
    "DEFAULT_REGION",
    "OFFER_ID_PATTERN",
    "OfferConfig",
    "PRODUCT_ID_MAX_LENGTH",
    "PRODUCT_ID_PATTERN",
    "PricingPhase",
    "RECURRENCE_FINITE",
    "RECURRENCE_INFINITE",
    "RECURRENCE_NON_RECURRING",
    "STATE_ACTIVE",
    "STATE_DRAFT",
    "STATE_INACTIVE",
    "SubscriptionManager",
    "VALID_RECURRENCE_MODES",
    "VALID_STATES",
    "standard_subscriptions",
    "validate_base_plan_id",
    "validate_billing_period",
    "validate_offer_id",
    "validate_product_id",
]


if __name__ == "__main__":
    sys.exit(_main())
