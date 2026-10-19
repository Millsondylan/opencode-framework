"""Google Play in app products and SKU management.

This module wraps the inappproducts resource of the Android Publisher
API v3 to create, list, update, delete, and bulk manage managed in app
products (IAPs) and subscriptions. SKUs are validated against Play
store formatting rules before any network call is made.

SKU format rules
    The Play store requires SKU identifiers that are lowercase, consist
    of letters, digits, and underscores, and are at most 40 characters.
    Identifiers that start with "android." or "com.google." are
    reserved by the platform and cannot be registered.

Purchase types
    managedUser:  one time purchase or managed product.
    subscription: auto renewing subscription (managed via subscriptions
        resource in the v3 API, but price and listing fields share the
        same shape used here for completeness).

Pricing
    Play prices are expressed in micros (1 USD = 1000000 micros). Each
    product has a defaultPrice and may include a prices map keyed by
    region code.

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

from publishing.play.client import (
    PlayAPIError,
    PlayAuthError,
    PlayClient,
    PlayValidationError,
    get_default_client,
)


_LOG = logging.getLogger("publishing.play.iap")
if not _LOG.handlers:
    _LOG.addHandler(logging.NullHandler())


PURCHASE_TYPE_MANAGED = "managedUser"
PURCHASE_TYPE_SUBSCRIPTION = "subscription"

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

VALID_PURCHASE_TYPES: set[str] = {
    PURCHASE_TYPE_MANAGED,
    PURCHASE_TYPE_SUBSCRIPTION,
}

VALID_STATUSES: set[str] = {STATUS_ACTIVE, STATUS_INACTIVE}

SKU_PATTERN = re.compile(r"^[a-z0-9_]{1,40}$")
SKU_MAX_LENGTH = 40

RESERVED_SKU_PREFIXES: tuple[str, ...] = (
    "android.",
    "com.google.",
    "com.android.",
)

DEFAULT_CURRENCY = "USD"


@dataclass
class SKUDefinition:
    """In app product SKU definition used for bulk provisioning.

    Attributes:
        sku: Lowercase identifier matching SKU_PATTERN.
        title: Human readable title, usually in en US locale.
        description: Short marketing description shown in the store.
        price_micros: Default price in micros (e.g. 990000 == 0.99).
        currency: ISO 4217 currency code for the default price.
        purchase_type: Either managedUser or subscription.
        status: Either active or inactive.
    """

    sku: str
    title: str
    description: str
    price_micros: int
    currency: str = DEFAULT_CURRENCY
    purchase_type: str = PURCHASE_TYPE_MANAGED
    status: str = STATUS_ACTIVE
    locale: str = "en-US"

    def to_kwargs(self, package_name: str) -> dict[str, Any]:
        """Return kwargs suitable for IAPManager.create_product."""
        return {
            "package_name": package_name,
            "sku": self.sku,
            "title": self.title,
            "description": self.description,
            "price_micros": int(self.price_micros),
            "currency": self.currency,
            "purchase_type": self.purchase_type,
            "status": self.status,
            "locale": self.locale,
        }


def validate_sku(sku: str) -> tuple[bool, str]:
    """Validate a Play store SKU identifier.

    Returns (is_valid, message). Checks character set, length, and
    reserved platform prefixes.
    """
    if sku is None or not isinstance(sku, str):
        return False, "sku must be a string"
    if not sku:
        return False, "sku is empty"
    if len(sku) > SKU_MAX_LENGTH:
        return False, "sku exceeds {0} characters (got {1})".format(
            SKU_MAX_LENGTH, len(sku)
        )
    if not SKU_PATTERN.match(sku):
        return False, (
            "sku must match ^[a-z0-9_]{1,40}$; only lowercase letters, "
            "digits, and underscores are allowed"
        )
    for prefix in RESERVED_SKU_PREFIXES:
        if sku.startswith(prefix):
            return False, "sku starts with reserved prefix: {0}".format(prefix)
    return True, "ok"


def _validate_price_micros(price_micros: Any) -> int:
    """Coerce and validate a price_micros value."""
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
    """Validate a currency code (ISO 4217 shape)."""
    if not isinstance(currency, str) or not currency:
        raise PlayValidationError("currency must be a non empty string")
    code = currency.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise PlayValidationError(
            "currency must be a 3 letter ISO 4217 code, got {0}".format(currency)
        )
    return code


def _listing_body(locale: str, title: str, description: str) -> dict[str, Any]:
    """Return a single localised listing entry."""
    if not locale:
        raise PlayValidationError("listing locale is required")
    if not title:
        raise PlayValidationError("listing title is required")
    if not description:
        raise PlayValidationError("listing description is required")
    return {locale: {"title": title, "description": description}}


class IAPManager:
    """Manage in app products for a Google Play application."""

    def __init__(self, client: Optional[PlayClient] = None) -> None:
        """Initialise the manager.

        Args:
            client: Authenticated PlayClient. When None, uses the module
                default client loaded from environment variables.
        """
        self.client = client if client is not None else get_default_client()

    def _package(self, override: Optional[str] = None) -> str:
        """Return the package name, preferring an explicit override."""
        if override:
            return override
        package = self.client.app_package_name
        if not package:
            raise PlayAuthError(
                "Application package name is not configured on PlayClient."
            )
        return package

    def list_products(self, package_name: Optional[str] = None) -> list[dict]:
        """List all in app products for the given package.

        Automatically paginates using the tokenPagination cursor.
        """
        package = self._package(package_name)
        products: list[dict] = []
        token: Optional[str] = None
        while True:
            kwargs: dict[str, Any] = {"packageName": package}
            if token:
                kwargs["token"] = token
            request = self.client.service.inappproducts().list(**kwargs)
            result = self.client.execute(
                request, operation="inappproducts.list"
            )
            if not isinstance(result, dict):
                break
            items = result.get("inappproduct") or result.get("inAppProduct") or []
            if isinstance(items, list):
                products.extend(items)
            pagination = result.get("tokenPagination") or {}
            next_token = pagination.get("nextPageToken") if isinstance(
                pagination, dict
            ) else None
            if not next_token:
                break
            token = next_token
        _LOG.info("inappproducts.list package=%s count=%d", package, len(products))
        return products

    def get_product(
        self,
        package_name: Optional[str],
        sku: str,
    ) -> dict:
        """Return a single in app product resource by SKU."""
        ok, message = validate_sku(sku)
        if not ok:
            raise PlayValidationError(
                "invalid sku {0}: {1}".format(sku, message)
            )
        package = self._package(package_name)
        request = self.client.service.inappproducts().get(
            packageName=package,
            sku=sku,
        )
        return self.client.execute(request, operation="inappproducts.get")

    def create_product(
        self,
        package_name: Optional[str],
        sku: str,
        title: str,
        description: str,
        price_micros: int,
        currency: str = DEFAULT_CURRENCY,
        purchase_type: str = PURCHASE_TYPE_MANAGED,
        status: str = STATUS_ACTIVE,
        locale: str = "en-US",
    ) -> dict:
        """Insert a new in app product with default pricing and listing."""
        ok, message = validate_sku(sku)
        if not ok:
            raise PlayValidationError(
                "invalid sku {0}: {1}".format(sku, message)
            )
        if purchase_type not in VALID_PURCHASE_TYPES:
            raise PlayValidationError(
                "purchase_type {0} must be one of {1}".format(
                    purchase_type, sorted(VALID_PURCHASE_TYPES)
                )
            )
        if status not in VALID_STATUSES:
            raise PlayValidationError(
                "status {0} must be one of {1}".format(
                    status, sorted(VALID_STATUSES)
                )
            )
        price_int = _validate_price_micros(price_micros)
        currency_code = _validate_currency(currency)
        package = self._package(package_name)
        body: dict[str, Any] = {
            "packageName": package,
            "sku": sku,
            "status": status,
            "purchaseType": purchase_type,
            "defaultPrice": {
                "priceMicros": str(price_int),
                "currency": currency_code,
            },
            "listings": _listing_body(locale, title, description),
            "defaultLanguage": locale,
        }
        request = self.client.service.inappproducts().insert(
            packageName=package,
            body=body,
        )
        result = self.client.execute(
            request, operation="inappproducts.insert"
        )
        _LOG.info(
            "inappproducts.insert sku=%s price_micros=%s currency=%s type=%s",
            sku,
            price_int,
            currency_code,
            purchase_type,
        )
        return result

    def update_product(
        self,
        package_name: Optional[str],
        sku: str,
        updates: dict[str, Any],
    ) -> dict:
        """Patch an existing in app product with a shallow merge.

        The updates dict is merged on top of the current resource. SKU,
        packageName, and server managed fields are always forced to
        their expected values.
        """
        ok, message = validate_sku(sku)
        if not ok:
            raise PlayValidationError(
                "invalid sku {0}: {1}".format(sku, message)
            )
        if not isinstance(updates, dict) or not updates:
            raise PlayValidationError(
                "updates must be a non empty dict"
            )
        package = self._package(package_name)
        current = self.get_product(package, sku)
        merged: dict[str, Any] = {}
        if isinstance(current, dict):
            merged.update(current)
        merged.update(updates)
        merged["packageName"] = package
        merged["sku"] = sku
        request = self.client.service.inappproducts().update(
            packageName=package,
            sku=sku,
            body=merged,
        )
        result = self.client.execute(
            request, operation="inappproducts.update"
        )
        _LOG.info("inappproducts.update sku=%s fields=%s", sku, sorted(updates))
        return result

    def delete_product(
        self,
        package_name: Optional[str],
        sku: str,
    ) -> None:
        """Delete an in app product by SKU."""
        ok, message = validate_sku(sku)
        if not ok:
            raise PlayValidationError(
                "invalid sku {0}: {1}".format(sku, message)
            )
        package = self._package(package_name)
        request = self.client.service.inappproducts().delete(
            packageName=package,
            sku=sku,
        )
        self.client.execute(request, operation="inappproducts.delete")
        _LOG.info("inappproducts.delete sku=%s", sku)

    def bulk_create_products(
        self,
        package_name: Optional[str],
        skus: list[dict[str, Any]],
    ) -> list[dict]:
        """Create multiple in app products sequentially.

        Each entry in skus is a dict of keyword arguments accepted by
        create_product, without package_name (which is provided once).

        Returns a list with the created product resource for each SKU,
        in input order.
        """
        if not isinstance(skus, list) or not skus:
            raise PlayValidationError(
                "skus must be a non empty list"
            )
        package = self._package(package_name)
        results: list[dict] = []
        for index, entry in enumerate(skus):
            if not isinstance(entry, dict):
                raise PlayValidationError(
                    "skus[{0}] must be a dict".format(index)
                )
            kwargs = dict(entry)
            kwargs.pop("package_name", None)
            try:
                product = self.create_product(package, **kwargs)
            except TypeError as exc:
                raise PlayValidationError(
                    "skus[{0}] invalid kwargs: {1}".format(index, exc)
                ) from exc
            results.append(product)
        _LOG.info("bulk_create_products count=%d", len(results))
        return results

    def set_regional_prices(
        self,
        package_name: Optional[str],
        sku: str,
        prices: dict[str, tuple[int, str]],
    ) -> dict:
        """Replace the regional price map for a product.

        Args:
            package_name: Target package (or None to use the default).
            sku: SKU to update.
            prices: Mapping of ISO 3166 region code to a tuple of
                (price_micros, currency).

        Returns the updated product resource.
        """
        ok, message = validate_sku(sku)
        if not ok:
            raise PlayValidationError(
                "invalid sku {0}: {1}".format(sku, message)
            )
        if not isinstance(prices, dict) or not prices:
            raise PlayValidationError(
                "prices must be a non empty dict"
            )
        price_body: dict[str, dict[str, str]] = {}
        for region, pair in prices.items():
            if not isinstance(region, str) or not region:
                raise PlayValidationError(
                    "region code must be a non empty string"
                )
            if (
                not isinstance(pair, (tuple, list))
                or len(pair) != 2
            ):
                raise PlayValidationError(
                    "prices[{0}] must be a (price_micros, currency) pair".format(region)
                )
            price_int = _validate_price_micros(pair[0])
            currency_code = _validate_currency(pair[1])
            price_body[region.upper()] = {
                "priceMicros": str(price_int),
                "currency": currency_code,
            }
        return self.update_product(
            package_name,
            sku,
            {"prices": price_body},
        )


def standard_sku_set() -> list[SKUDefinition]:
    """Return a small standard SKU set useful for tests and first runs."""
    return [
        SKUDefinition(
            sku="unlock_pro",
            title="Unlock Pro",
            description="Unlock all premium features.",
            price_micros=4_990_000,
            currency="USD",
            purchase_type=PURCHASE_TYPE_MANAGED,
            status=STATUS_ACTIVE,
        ),
        SKUDefinition(
            sku="unlock_themes",
            title="Theme Pack",
            description="Unlock the full theme collection.",
            price_micros=1_990_000,
            currency="USD",
            purchase_type=PURCHASE_TYPE_MANAGED,
            status=STATUS_ACTIVE,
        ),
        SKUDefinition(
            sku="remove_ads",
            title="Remove Ads",
            description="Permanently remove advertisements.",
            price_micros=2_990_000,
            currency="USD",
            purchase_type=PURCHASE_TYPE_MANAGED,
            status=STATUS_ACTIVE,
        ),
    ]


def _load_sku_file(path: str) -> list[dict[str, Any]]:
    """Load a JSON array of SKU kwargs for bulk creation."""
    from pathlib import Path as _Path

    file_path = _Path(path).expanduser()
    if not file_path.is_file():
        raise PlayValidationError(
            "sku file not found: {0}".format(file_path)
        )
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PlayValidationError(
            "failed to read sku file {0}: {1}".format(file_path, exc)
        ) from exc
    if not isinstance(data, list):
        raise PlayValidationError("sku file must contain a JSON array")
    return data


def _main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for IAP and SKU management."""
    parser = argparse.ArgumentParser(
        prog="publishing.play.iap",
        description="Manage Google Play in app products and SKUs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_cmd = subparsers.add_parser(
        "validate-sku", help="Validate a SKU identifier."
    )
    validate_cmd.add_argument("--sku", required=True)
    validate_cmd.set_defaults(handler="validate-sku")

    standard_cmd = subparsers.add_parser(
        "standard", help="Print the standard SKU set as JSON."
    )
    standard_cmd.set_defaults(handler="standard")

    list_cmd = subparsers.add_parser(
        "list", help="List all in app products for the configured package."
    )
    list_cmd.add_argument("--package", required=False, default=None)
    list_cmd.set_defaults(handler="list")

    bulk_cmd = subparsers.add_parser(
        "bulk-create",
        help="Bulk create in app products from a JSON array file.",
    )
    bulk_cmd.add_argument("--package", required=False, default=None)
    bulk_cmd.add_argument("--file", required=True)
    bulk_cmd.set_defaults(handler="bulk-create")

    args = parser.parse_args(argv)

    if args.handler == "validate-sku":
        ok, message = validate_sku(args.sku)
        print(json.dumps({"ok": ok, "message": message}, indent=2))
        return 0 if ok else 1
    if args.handler == "standard":
        payload = [
            {
                "sku": s.sku,
                "title": s.title,
                "description": s.description,
                "price_micros": s.price_micros,
                "currency": s.currency,
                "purchase_type": s.purchase_type,
                "status": s.status,
            }
            for s in standard_sku_set()
        ]
        print(json.dumps(payload, indent=2))
        return 0
    if args.handler == "list":
        manager = IAPManager()
        products = manager.list_products(args.package)
        print(json.dumps({"count": len(products)}, indent=2))
        return 0
    if args.handler == "bulk-create":
        entries = _load_sku_file(args.file)
        manager = IAPManager()
        created = manager.bulk_create_products(args.package, entries)
        print(json.dumps({"created": len(created)}, indent=2))
        return 0
    parser.error("unknown command")
    return 2


__all__ = [
    "DEFAULT_CURRENCY",
    "IAPManager",
    "PURCHASE_TYPE_MANAGED",
    "PURCHASE_TYPE_SUBSCRIPTION",
    "RESERVED_SKU_PREFIXES",
    "SKUDefinition",
    "SKU_MAX_LENGTH",
    "SKU_PATTERN",
    "STATUS_ACTIVE",
    "STATUS_INACTIVE",
    "VALID_PURCHASE_TYPES",
    "VALID_STATUSES",
    "standard_sku_set",
    "validate_sku",
]


if __name__ == "__main__":
    sys.exit(_main())
