"""Dry-run test for Play API v3. Validates workflow structure without publishing.

This test exercises the high level workflow of the Play publishing modules
(client, release, listing, iap, subs) without performing any real HTTP calls.
It uses a MockPlayClient that records every API call as a tuple so the test
can assert shape and ordering.

Run this directly to see PASS/FAIL for each test, or call run_all_tests() to
get a (passed, failed) tuple. Exits with status 0 on full success and 1 on
any failure. If google-api-python-client or google-auth are missing the test
SKIPs with exit code 0 and prints the install instruction.
"""

from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Optional


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _check_deps() -> tuple[bool, str]:
    """Return (installed, message). Does not raise."""
    try:
        import google.oauth2  # noqa: F401
        import googleapiclient  # noqa: F401
        return True, "ok"
    except ImportError as exc:
        return False, (
            "SKIP: google-api-python-client and google-auth are not installed. "
            "Install via: pip install google-api-python-client google-auth. "
            "Original import error: {0}".format(exc)
        )


_DEPS_OK, _DEPS_MSG = _check_deps()

if not _DEPS_OK:
    print(_DEPS_MSG)
    sys.exit(0)


from publishing.play.client import PlayClient, PlayValidationError  # noqa: E402
from publishing.play.release import (  # noqa: E402
    ReleaseManager,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    TRACK_BETA,
    TRACK_INTERNAL,
    validate_closed_testing_requirements,
)
from publishing.play.listing import (  # noqa: E402
    ListingManager,
    validate_listing_fields,
)
from publishing.play.iap import (  # noqa: E402
    IAPManager,
    validate_sku,
)
from publishing.play.subs import SubscriptionManager  # noqa: E402


class _MockRequest:
    """Stand in for a googleapiclient HttpRequest with a canned response."""

    def __init__(self, canned: Any) -> None:
        self._canned = canned

    def execute(self) -> Any:
        return self._canned


class MockPlayClient:
    """Duck typed PlayClient that records every call without hitting HTTP.

    Each method returns a _MockRequest so the caller can still invoke
    execute on it. Every API call name and its kwargs are appended to
    self.calls for later assertion.
    """

    def __init__(self, package: str = "com.example.fake") -> None:
        self.app_package_name = package
        self.service_account_json_path = "/tmp/fake_sa.json"
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._edit_counter = 0
        self._version_counter = 1000
        self._tracks: dict[str, dict[str, Any]] = {}
        self._subscriptions: dict[str, dict[str, Any]] = {}

    def _record(self, operation: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((operation, dict(kwargs)))

    def _require_package(self) -> str:
        return self.app_package_name

    def execute(self, request: Any, *, operation: str = "execute") -> Any:
        if isinstance(request, _MockRequest):
            return request.execute()
        return {}

    def edits_insert(self) -> dict:
        self._edit_counter += 1
        edit_id = "mock_edit_{0}".format(self._edit_counter)
        self._record("edits.insert", {"packageName": self.app_package_name})
        return {"id": edit_id, "expiryTimeSeconds": "9999999999"}

    def edits_commit(self, edit_id: str, validate_only: bool = False) -> dict:
        op = "edits.commit.validate_only" if validate_only else "edits.commit"
        self._record(op, {"editId": edit_id, "validateOnly": validate_only})
        return {"id": edit_id, "committed": not validate_only}

    def edits_validate(self, edit_id: str) -> dict:
        self._record("edits.validate", {"editId": edit_id})
        return {"id": edit_id}

    def edits_delete(self, edit_id: str) -> None:
        self._record("edits.delete", {"editId": edit_id})

    def edits_get(self, edit_id: str) -> dict:
        self._record("edits.get", {"editId": edit_id})
        return {"id": edit_id}

    @property
    def service(self) -> Any:
        return _MockService(self)


class _MockService:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def edits(self) -> "_MockEdits":
        return _MockEdits(self._c)

    def inappproducts(self) -> "_MockInappProducts":
        return _MockInappProducts(self._c)

    def monetization(self) -> "_MockMonetization":
        return _MockMonetization(self._c)


class _MockEdits:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def bundles(self) -> "_MockBundles":
        return _MockBundles(self._c)

    def tracks(self) -> "_MockTracks":
        return _MockTracks(self._c)

    def listings(self) -> "_MockListings":
        return _MockListings(self._c)

    def images(self) -> "_MockImages":
        return _MockImages(self._c)


class _MockBundles:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def upload(self, **kwargs: Any) -> _MockRequest:
        self._c._version_counter += 1
        code = self._c._version_counter
        self._c._record("edits.bundles.upload", kwargs)
        return _MockRequest({"versionCode": code, "sha1": "deadbeef"})


class _MockTracks:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def get(self, **kwargs: Any) -> _MockRequest:
        track = kwargs.get("track")
        self._c._record("edits.tracks.get", kwargs)
        stored = self._c._tracks.get(track, {"track": track, "releases": []})
        return _MockRequest(dict(stored))

    def update(self, **kwargs: Any) -> _MockRequest:
        track = kwargs.get("track")
        body = kwargs.get("body") or {}
        self._c._tracks[track] = dict(body)
        self._c._record("edits.tracks.update", kwargs)
        return _MockRequest(dict(body))


class _MockListings:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def get(self, **kwargs: Any) -> _MockRequest:
        self._c._record("edits.listings.get", kwargs)
        return _MockRequest({"language": kwargs.get("language")})

    def update(self, **kwargs: Any) -> _MockRequest:
        self._c._record("edits.listings.update", kwargs)
        body = kwargs.get("body") or {}
        return _MockRequest(dict(body))


class _MockImages:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def upload(self, **kwargs: Any) -> _MockRequest:
        self._c._record("edits.images.upload", kwargs)
        return _MockRequest({"image": {"id": "img_1"}})

    def deleteall(self, **kwargs: Any) -> _MockRequest:
        self._c._record("edits.images.deleteall", kwargs)
        return _MockRequest({"deleted": True})


class _MockInappProducts:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def list(self, **kwargs: Any) -> _MockRequest:
        self._c._record("inappproducts.list", kwargs)
        return _MockRequest({"inappproduct": []})

    def get(self, **kwargs: Any) -> _MockRequest:
        self._c._record("inappproducts.get", kwargs)
        return _MockRequest({"sku": kwargs.get("sku")})

    def insert(self, **kwargs: Any) -> _MockRequest:
        self._c._record("inappproducts.insert", kwargs)
        body = kwargs.get("body") or {}
        return _MockRequest(dict(body))

    def update(self, **kwargs: Any) -> _MockRequest:
        self._c._record("inappproducts.update", kwargs)
        body = kwargs.get("body") or {}
        return _MockRequest(dict(body))

    def delete(self, **kwargs: Any) -> _MockRequest:
        self._c._record("inappproducts.delete", kwargs)
        return _MockRequest({})


class _MockMonetization:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def subscriptions(self) -> "_MockSubscriptions":
        return _MockSubscriptions(self._c)


class _MockSubscriptions:
    def __init__(self, client: MockPlayClient) -> None:
        self._c = client

    def list(self, **kwargs: Any) -> _MockRequest:
        self._c._record("monetization.subscriptions.list", kwargs)
        return _MockRequest({"subscriptions": []})

    def get(self, **kwargs: Any) -> _MockRequest:
        pid = kwargs.get("productId")
        self._c._record("monetization.subscriptions.get", kwargs)
        stored = self._c._subscriptions.get(pid, {"productId": pid, "basePlans": []})
        return _MockRequest(dict(stored))

    def create(self, **kwargs: Any) -> _MockRequest:
        pid = kwargs.get("productId")
        body = kwargs.get("body") or {}
        self._c._subscriptions[pid] = dict(body)
        self._c._record("monetization.subscriptions.create", kwargs)
        return _MockRequest(dict(body))

    def patch(self, **kwargs: Any) -> _MockRequest:
        pid = kwargs.get("productId")
        body = kwargs.get("body") or {}
        self._c._subscriptions[pid] = dict(body)
        self._c._record("monetization.subscriptions.patch", kwargs)
        return _MockRequest(dict(body))

    def archive(self, **kwargs: Any) -> _MockRequest:
        self._c._record("monetization.subscriptions.archive", kwargs)
        return _MockRequest({"archived": True})


def test_edit_lifecycle() -> None:
    """Create an edit and commit in validate_only mode."""
    client = MockPlayClient()
    edit = client.edits_insert()
    assert edit["id"] == "mock_edit_1", "expected mock edit id, got {0}".format(edit)
    result = client.edits_commit(edit["id"], validate_only=True)
    assert result["committed"] is False, "validate_only should not commit"
    ops = [c[0] for c in client.calls]
    assert "edits.insert" in ops, "edits.insert not recorded"
    assert "edits.commit.validate_only" in ops, "validate_only commit not recorded"


def test_upload_aab_flow() -> None:
    """Upload a tempfile AAB via ReleaseManager and assert version code."""
    client = MockPlayClient()
    manager = ReleaseManager(client)
    edit = client.edits_insert()
    with tempfile.NamedTemporaryFile(
        suffix=".aab", prefix="fake_bundle_", delete=False
    ) as handle:
        handle.write(b"FAKEAAB" * 16)
        tmp_path = handle.name
    try:
        result = manager.upload_aab(edit["id"], tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    assert isinstance(result, dict), "upload result must be dict"
    assert result.get("versionCode") is not None, "version code missing"
    assert result["versionCode"] > 1000, "version code too low: {0}".format(result)
    ops = [c[0] for c in client.calls]
    assert "edits.bundles.upload" in ops, "upload not recorded"


def test_update_track_rollout() -> None:
    """Update internal track with rollout=0.5, assert inProgress + userFraction."""
    client = MockPlayClient()
    manager = ReleaseManager(client)
    edit = client.edits_insert()
    manager.update_track(
        edit_id=edit["id"],
        track=TRACK_INTERNAL,
        version_codes=[1001],
        release_name="Internal Test v1",
        release_notes=[{"language": "en-US", "text": "Internal test build."}],
        rollout_percentage=0.5,
    )
    stored = client._tracks.get(TRACK_INTERNAL)
    assert stored is not None, "internal track not stored"
    release = stored["releases"][0]
    assert release["status"] == STATUS_IN_PROGRESS, (
        "expected inProgress status, got {0}".format(release["status"])
    )
    assert abs(float(release["userFraction"]) - 0.5) < 1e-9, (
        "userFraction should be 0.5, got {0}".format(release["userFraction"])
    )


def test_update_track_full_rollout() -> None:
    """Update track with rollout=1.0, assert status=completed and no userFraction."""
    client = MockPlayClient()
    manager = ReleaseManager(client)
    edit = client.edits_insert()
    manager.update_track(
        edit_id=edit["id"],
        track=TRACK_INTERNAL,
        version_codes=[1002],
        release_name="Full rollout",
        release_notes=[{"language": "en-US", "text": "Full rollout."}],
        rollout_percentage=1.0,
    )
    stored = client._tracks.get(TRACK_INTERNAL)
    release = stored["releases"][0]
    assert release["status"] == STATUS_COMPLETED, (
        "expected completed status, got {0}".format(release["status"])
    )


def test_promote_internal_to_closed() -> None:
    """Promote internal to beta and assert version codes are carried across."""
    client = MockPlayClient()
    manager = ReleaseManager(client)
    edit = client.edits_insert()
    manager.update_track(
        edit_id=edit["id"],
        track=TRACK_INTERNAL,
        version_codes=[1010, 1011],
        release_name="internal",
        release_notes=[{"language": "en-US", "text": "internal."}],
        rollout_percentage=1.0,
    )
    manager.promote(edit["id"], TRACK_INTERNAL, TRACK_BETA)
    beta = client._tracks.get(TRACK_BETA)
    assert beta is not None, "beta track not populated after promote"
    beta_release = beta["releases"][0]
    codes = [int(c) for c in beta_release.get("versionCodes", [])]
    assert codes == [1010, 1011], "codes not copied: got {0}".format(codes)


def test_closed_testing_validation_fail() -> None:
    """11 testers over 14 days fails the closed testing policy."""
    releases = [{"status": STATUS_IN_PROGRESS}]
    ok, reason = validate_closed_testing_requirements(releases, testers=11, days_elapsed=14)
    assert ok is False, "should fail with fewer than 12 testers"
    assert "testers" in reason.lower(), "reason should mention testers: {0}".format(reason)


def test_closed_testing_validation_pass() -> None:
    """12 testers and 14 days passes the closed testing policy."""
    releases = [{"status": STATUS_COMPLETED}]
    ok, reason = validate_closed_testing_requirements(releases, testers=12, days_elapsed=14)
    assert ok is True, "should pass with 12 testers and 14 days: {0}".format(reason)


def test_listing_update() -> None:
    """Valid listing fields within limits should update successfully."""
    client = MockPlayClient()
    manager = ListingManager(client)
    edit = client.edits_insert()
    title = "My App Title"
    short = "A short marketing description."
    full = "A much longer description that stays well under 4000 characters."
    result = manager.update_listing(
        edit_id=edit["id"],
        language="en-US",
        title=title,
        short_desc=short,
        full_desc=full,
    )
    assert isinstance(result, dict), "listing update should return dict"
    ops = [c[0] for c in client.calls]
    assert "edits.listings.update" in ops, "listings update not recorded"


def test_listing_title_too_long() -> None:
    """Title longer than 30 characters should raise PlayValidationError."""
    client = MockPlayClient()
    manager = ListingManager(client)
    edit = client.edits_insert()
    long_title = "x" * 31
    raised = False
    try:
        manager.update_listing(
            edit_id=edit["id"],
            language="en-US",
            title=long_title,
            short_desc="short",
            full_desc="full",
        )
    except PlayValidationError:
        raised = True
    assert raised, "long title should raise PlayValidationError"


def test_iap_sku_validation() -> None:
    """SKU rules: valid lowercase passes, uppercase/long/reserved fail."""
    ok, _ = validate_sku("unlock_pro")
    assert ok, "lowercase alphanumeric sku should pass"
    ok, _ = validate_sku("UNLOCK_PRO")
    assert not ok, "uppercase should fail"
    ok, _ = validate_sku("a" * 41)
    assert not ok, "over length sku should fail"
    ok, _ = validate_sku("android.test")
    assert not ok, "reserved android. prefix should fail"
    ok, _ = validate_sku("com.google.test_sku")
    assert not ok, "reserved com.google. prefix should fail"


def test_iap_create() -> None:
    """create_product should record insert with expected body shape."""
    client = MockPlayClient()
    manager = IAPManager(client)
    result = manager.create_product(
        package_name=None,
        sku="unlock_pro",
        title="Unlock Pro",
        description="All premium features.",
        price_micros=4_990_000,
        currency="USD",
    )
    assert isinstance(result, dict)
    ops = [c for c in client.calls if c[0] == "inappproducts.insert"]
    assert ops, "inappproducts.insert not recorded"
    body = ops[0][1].get("body") or {}
    assert body.get("sku") == "unlock_pro", "sku mismatch in body"
    assert body.get("defaultPrice", {}).get("priceMicros") == "4990000", (
        "priceMicros mismatch: {0}".format(body.get("defaultPrice"))
    )
    assert body.get("defaultPrice", {}).get("currency") == "USD", "currency mismatch"


def test_subscription_add_base_plan() -> None:
    """add_base_plan should produce an autoRenewingBasePlanType with P1M period."""
    client = MockPlayClient()
    manager = SubscriptionManager(client)
    manager.create_subscription(
        package_name=None,
        product_id="sub_pro_monthly",
        title="Pro Monthly",
        description="Monthly pro subscription.",
    )
    manager.add_base_plan(
        package_name=None,
        product_id="sub_pro_monthly",
        base_plan_id="monthly-autorenew",
        auto_renewing=True,
        billing_period="P1M",
        price_micros=4_990_000,
        currency="USD",
    )
    patch_calls = [c for c in client.calls if c[0] == "monetization.subscriptions.patch"]
    assert patch_calls, "patch not recorded"
    body = patch_calls[-1][1].get("body") or {}
    plans = body.get("basePlans") or []
    assert plans, "basePlans missing"
    plan = plans[-1]
    assert plan.get("basePlanId") == "monthly-autorenew", (
        "basePlanId mismatch: {0}".format(plan.get("basePlanId"))
    )
    auto = plan.get("autoRenewingBasePlanType") or {}
    assert auto.get("billingPeriodDuration") == "P1M", (
        "billingPeriodDuration should be P1M: {0}".format(auto)
    )


def _run_one(name: str, fn: Any) -> bool:
    """Run one test function, printing PASS or FAIL and returning bool."""
    try:
        fn()
    except AssertionError as exc:
        print("FAIL {0}: {1}".format(name, exc))
        return False
    except Exception as exc:
        print("FAIL {0}: unexpected {1}".format(name, exc))
        traceback.print_exc()
        return False
    print("PASS {0}".format(name))
    return True


def run_all_tests() -> tuple[int, int]:
    """Run every test_ function in this module. Return (passed, failed)."""
    cases = [
        ("test_edit_lifecycle", test_edit_lifecycle),
        ("test_upload_aab_flow", test_upload_aab_flow),
        ("test_update_track_rollout", test_update_track_rollout),
        ("test_update_track_full_rollout", test_update_track_full_rollout),
        ("test_promote_internal_to_closed", test_promote_internal_to_closed),
        ("test_closed_testing_validation_fail", test_closed_testing_validation_fail),
        ("test_closed_testing_validation_pass", test_closed_testing_validation_pass),
        ("test_listing_update", test_listing_update),
        ("test_listing_title_too_long", test_listing_title_too_long),
        ("test_iap_sku_validation", test_iap_sku_validation),
        ("test_iap_create", test_iap_create),
        ("test_subscription_add_base_plan", test_subscription_add_base_plan),
    ]
    passed = 0
    failed = 0
    for name, fn in cases:
        if _run_one(name, fn):
            passed += 1
        else:
            failed += 1
    return passed, failed


if __name__ == "__main__":
    p, f = run_all_tests()
    total = p + f
    print("{0}/{1} PASSED".format(p, total))
    sys.exit(0 if f == 0 else 1)
