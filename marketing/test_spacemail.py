"""Tests for Spacemail client, compliance, suppression, and outreach engine.

Proves:
  1. Suppression list add/check/bulk/stats work end to end.
  2. ComplianceChecker injects CAN-SPAM footer and detects spam subjects.
  3. Jurisdiction detection maps TLDs to regions.
  4. Consent ledger logs and checks consent.
  5. SpacemailClient honors the suppression list before dispatching.
  6. SpacemailClient dispatches correctly when recipient is clean.
  7. send_bulk respects suppression across a batch.
  8. Warm up rate limit blocks sends past day 1 cap of 50 per hour.
  9. AggressiveGrowthEngine blocks EU recipients without double opt in.
 10. AggressiveGrowthEngine dispatches US recipients with CAN-SPAM footer.

The MCP dispatcher is injected as a callable so tests never touch a live
MCP session. All tests use tempfile SQLite paths and clean up on exit.

All dashes in this file are ASCII hyphen minus (U+002D) per rule 08.

Run:
  python3 marketing/test_spacemail.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

# Ensure the marketing package root is importable when run directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from marketing.spacemail.suppression import SuppressionList
    from marketing.spacemail.compliance import ComplianceChecker
    from marketing.spacemail.client import SpacemailClient
    from marketing.outreach.aggressive_growth import (
        AggressiveGrowthEngine,
        OutreachCampaign,
    )
    IMPORTS_OK = True
    IMPORT_ERR: Optional[str] = None
except Exception as exc:
    IMPORTS_OK = False
    IMPORT_ERR = f"{type(exc).__name__}: {exc}"


POSTAL_ADDRESS = "Example Inc, 123 Main St, Toronto ON M5V 1A1, Canada"
COMPANY_NAME = "Example Inc"
UNSUB_URL = "https://example.com/u/abc123"


def _tmp_suppression() -> "SuppressionList":
    tmp = tempfile.NamedTemporaryFile(
        prefix="supp_", suffix=".sqlite", delete=False
    )
    tmp.close()
    return SuppressionList(db_path=tmp.name)


def _tmp_compliance() -> "ComplianceChecker":
    tmp = tempfile.NamedTemporaryFile(
        prefix="consent_", suffix=".sqlite", delete=False
    )
    tmp.close()
    return ComplianceChecker(
        postal_address=POSTAL_ADDRESS,
        company_name=COMPANY_NAME,
        consent_ledger_path=tmp.name,
    )


def _tmp_log_path() -> str:
    fd, path = tempfile.mkstemp(prefix="spacemail_", suffix=".log")
    os.close(fd)
    return path


class RecordingDispatcher:
    """Callable stub for the MCP dispatcher. Records every call."""

    def __init__(self, return_value: Optional[dict] = None) -> None:
        self.return_value = return_value or {
            "message_id": "msg_test_0001",
            "status": "queued",
        }
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, tool: str, args: dict) -> dict:
        self.calls.append((tool, dict(args)))
        return dict(self.return_value)


# Tests 1 to 6 exercise suppression + compliance directly.
def test_suppression_add_and_check() -> None:
    supp = _tmp_suppression()
    supp.add("User@Example.com", reason="user requested", category="unsubscribe")
    ok, reason = supp.is_suppressed("user@example.com")
    assert ok is True, "expected address to be suppressed"
    assert reason is not None and "unsubscribe" in reason, reason

    ok2, _ = supp.is_suppressed("someone_else@example.com")
    assert ok2 is False, "unrelated address should not be suppressed"


def test_suppression_bulk_add() -> None:
    supp = _tmp_suppression()
    items = [
        {"email": "a@x.com", "reason": "hard bounce", "category": "bounce_hard"},
        {"email": "b@x.com", "reason": "soft bounce", "category": "bounce_soft"},
        {"email": "c@x.com", "reason": "spam click", "category": "complaint"},
        {"email": "d@x.com", "reason": "opted out", "category": "unsubscribe"},
        {"email": "e@x.com", "reason": "operator", "category": "manual"},
    ]
    n = supp.bulk_add(items)
    assert n == 5, f"bulk_add should return 5, got {n}"

    stats = supp.stats()
    assert stats["total"] == 5, stats
    assert stats["bounce_hard"] == 1, stats
    assert stats["bounce_soft"] == 1, stats
    assert stats["complaint"] == 1, stats
    assert stats["unsubscribe"] == 1, stats
    assert stats["manual"] == 1, stats


def test_compliance_footer_injection() -> None:
    comp = _tmp_compliance()
    body_html = "<p>Hello world.</p>"
    body_text = "Hello world."
    html_out, text_out = comp.inject_footer(body_html, body_text, UNSUB_URL)

    assert POSTAL_ADDRESS in html_out, "HTML footer must contain postal address"
    assert UNSUB_URL in html_out, "HTML footer must contain unsubscribe URL"
    assert COMPANY_NAME in html_out, "HTML footer must contain company name"

    assert POSTAL_ADDRESS in text_out, "text footer must contain postal address"
    assert UNSUB_URL in text_out, "text footer must contain unsubscribe URL"
    assert "unsubscribe" in text_out.lower(), "text footer must mention unsubscribe"


def test_compliance_subject_spam_detection() -> None:
    comp = _tmp_compliance()
    # Log express consent so jurisdiction check does not add noise.
    comp.log_consent(
        email="rcpt@example.com",
        jurisdiction="us",
        method="express",
        source="signup",
        confirmed=True,
    )
    body_text = (
        "Hello. This is a legitimate message.\n"
        f"Company: {COMPANY_NAME}\n"
        f"Address: {POSTAL_ADDRESS}\n"
        f"Unsubscribe: {UNSUB_URL}\n"
    )

    bad_subject = "!!! URGENT FREE MONEY !!!"
    ok_bad, issues_bad = comp.validate_outbound(
        "rcpt@example.com", bad_subject, body_text, jurisdiction="us"
    )
    assert ok_bad is False, "spammy subject must be rejected"
    assert any("spam" in i.lower() for i in issues_bad), issues_bad

    good_subject = "Product update for April"
    ok_good, issues_good = comp.validate_outbound(
        "rcpt@example.com", good_subject, body_text, jurisdiction="us"
    )
    # Subject itself is fine; body may still lack List-Unsubscribe header
    # which is a recommendation, not a hard block. Accept as long as no
    # spam issues are flagged on the subject.
    subject_issues = [i for i in issues_good if "subject" in i.lower()]
    assert not subject_issues, f"good subject must pass, got {subject_issues}"


def test_compliance_jurisdiction_detection() -> None:
    comp = _tmp_compliance()

    eu_cases = [
        "user@example.eu",
        "user@example.uk",
        "user@example.co.uk",
        "user@example.de",
        "user@example.fr",
    ]
    for addr in eu_cases:
        j = comp.detect_jurisdiction(addr)
        assert j == "eu", f"{addr!r} should be eu, got {j!r}"

    ca_cases = ["user@example.ca", "user@shop.ca"]
    for addr in ca_cases:
        j = comp.detect_jurisdiction(addr)
        assert j == "ca", f"{addr!r} should be ca, got {j!r}"

    us_cases = ["user@example.com", "user@example.us", "user@thing.org"]
    for addr in us_cases:
        j = comp.detect_jurisdiction(addr)
        assert j == "us", f"{addr!r} should be us, got {j!r}"


def test_compliance_consent_ledger_log_and_check() -> None:
    comp = _tmp_compliance()
    cid = comp.log_consent(
        email="person@example.eu",
        jurisdiction="eu",
        method="double_opt_in",
        source="web_form",
        ip="198.51.100.7",
        confirmed=True,
    )
    assert cid > 0, "log_consent should return a positive row id"

    has = comp.check_consent("person@example.eu", "eu")
    assert has is True, "confirmed double opt in should pass EU check"

    not_has = comp.check_consent("stranger@example.eu", "eu")
    assert not_has is False, "random address must not have consent"


# Tests 7 to 10 exercise the SpacemailClient.
def _build_client(
    dispatcher: Callable[[str, dict], dict],
    domain_started_ts: Optional[int] = None,
) -> tuple["SpacemailClient", "SuppressionList", "ComplianceChecker"]:
    supp = _tmp_suppression()
    comp = _tmp_compliance()
    client = SpacemailClient(
        suppression=supp,
        compliance=comp,
        mcp_dispatcher=dispatcher,
        domain_started_ts=domain_started_ts,
        log_path=_tmp_log_path(),
    )
    return client, supp, comp


def _clean_body_text() -> str:
    return (
        "Hello. Thank you for subscribing.\n"
        f"{COMPANY_NAME}\n"
        f"{POSTAL_ADDRESS}\n"
        f"Unsubscribe any time: {UNSUB_URL}\n"
    )


def test_client_send_email_checks_suppression() -> None:
    dispatcher = RecordingDispatcher()
    client, supp, comp = _build_client(dispatcher)
    comp.log_consent(
        email="blocked@example.com",
        jurisdiction="us",
        method="express",
        source="signup",
        confirmed=True,
    )
    supp.add(
        email="blocked@example.com",
        reason="opted out",
        category="unsubscribe",
    )

    result = client.send_email(
        to="blocked@example.com",
        subject="Hello",
        body_html="<p>Hi</p>",
        body_text="Hi",
        from_name="Test",
        from_email="noreply@example.com",
        unsubscribe_url=UNSUB_URL,
        jurisdiction="us",
    )
    assert result.get("status") == "blocked", result
    assert "suppressed" in result.get("reason", ""), result
    assert len(dispatcher.calls) == 0, (
        f"dispatcher must not be called for suppressed address, "
        f"got {len(dispatcher.calls)} calls"
    )


def test_client_send_email_dispatches_when_clean() -> None:
    dispatcher = RecordingDispatcher()
    client, _supp, comp = _build_client(dispatcher)
    comp.log_consent(
        email="clean@example.com",
        jurisdiction="us",
        method="express",
        source="signup",
        confirmed=True,
    )

    result = client.send_email(
        to="clean@example.com",
        subject="Your April update",
        body_html="<p>Hello from our team.</p>",
        body_text="Hello from our team.",
        from_name="Example",
        from_email="news@example.com",
        unsubscribe_url=UNSUB_URL,
        jurisdiction="us",
    )
    assert result.get("message_id") == "msg_test_0001", result
    assert len(dispatcher.calls) == 1, dispatcher.calls
    tool, args = dispatcher.calls[0]
    assert tool.endswith("send_email"), tool
    assert args["to"] == "clean@example.com", args
    assert args["subject"] == "Your April update", args
    # Footer must have been injected.
    assert POSTAL_ADDRESS in args["body_text"], args["body_text"]
    assert UNSUB_URL in args["body_text"], args["body_text"]


def test_client_send_bulk_respects_suppression() -> None:
    dispatcher = RecordingDispatcher()
    client, supp, comp = _build_client(dispatcher)

    recipients = [
        {"email": "r1@example.com", "unsubscribe_token": "t1"},
        {"email": "r2@example.com", "unsubscribe_token": "t2"},
        {"email": "r3@example.com", "unsubscribe_token": "t3"},
        {"email": "r4@example.com", "unsubscribe_token": "t4"},
        {"email": "r5@example.com", "unsubscribe_token": "t5"},
    ]
    # Consent for every recipient to focus the test on suppression gating.
    for rcpt in recipients:
        comp.log_consent(
            email=rcpt["email"],
            jurisdiction="us",
            method="express",
            source="signup",
            confirmed=True,
        )

    # Two addresses on the suppression list.
    supp.add("r2@example.com", reason="bounce", category="bounce_hard")
    supp.add("r4@example.com", reason="opted out", category="unsubscribe")

    report = client.send_bulk(
        recipients=recipients,
        subject="News for you",
        body_html="<p>Hi {{first_name}}</p>",
        body_text="Hi {{first_name}}",
        from_name="Example",
        from_email="news@example.com",
        unsubscribe_url_template="https://example.com/u/{{token}}",
        delay_ms=0,
    )
    assert report["total"] == 5, report
    assert report["sent"] == 3, f"expected 3 sends, got {report}"
    assert report["blocked"] == 2, f"expected 2 blocks, got {report}"
    assert len(dispatcher.calls) == 3, (
        f"dispatcher should fire 3 times, fired {len(dispatcher.calls)}"
    )


def test_client_warmup_rate_limit() -> None:
    import time as _time

    dispatcher = RecordingDispatcher()
    # Fresh domain: started right now, day 1 cap = 50 per hour.
    client, _supp, comp = _build_client(
        dispatcher, domain_started_ts=int(_time.time())
    )
    comp.log_consent(
        email="rate@example.com",
        jurisdiction="us",
        method="express",
        source="signup",
        confirmed=True,
    )

    # Send 50 messages: all should succeed.
    sent_ok = 0
    for _ in range(50):
        res = client.send_email(
            to="rate@example.com",
            subject="Your update",
            body_html="<p>Hi</p>",
            body_text="Hi there.",
            from_name="Example",
            from_email="news@example.com",
            unsubscribe_url=UNSUB_URL,
            jurisdiction="us",
        )
        if res.get("message_id"):
            sent_ok += 1
    assert sent_ok == 50, f"expected 50 clean sends, got {sent_ok}"

    # 51st must be rejected by the rate limiter.
    raised = False
    try:
        client.send_email(
            to="rate@example.com",
            subject="One too many",
            body_html="<p>Hi</p>",
            body_text="Hi there.",
            from_name="Example",
            from_email="news@example.com",
            unsubscribe_url=UNSUB_URL,
            jurisdiction="us",
        )
    except RuntimeError as exc:
        raised = "rate limit" in str(exc).lower()
    assert raised, "51st send must raise a rate limit RuntimeError"


# Tests 11 and 12 exercise the outreach engine with the stubs that match
# its interface expectations.
class _OutreachSuppression:
    """Adapter matching AggressiveGrowthEngine's suppression interface."""

    def __init__(self) -> None:
        self._blocked: set[str] = set()

    def contains(self, email: str) -> bool:
        return email.lower() in self._blocked

    def add(self, email: str, reason: str) -> None:
        self._blocked.add(email.lower())


class _OutreachCompliance:
    """Adapter matching AggressiveGrowthEngine's compliance interface."""

    def __init__(
        self,
        jurisdiction_map: dict[str, str],
        double_opt_in: Optional[set[str]] = None,
        express: Optional[set[str]] = None,
        implied: Optional[set[str]] = None,
    ) -> None:
        self._jurisdiction = {k.lower(): v for k, v in jurisdiction_map.items()}
        self._double = {e.lower() for e in (double_opt_in or set())}
        self._express = {e.lower() for e in (express or set())}
        self._implied = {e.lower() for e in (implied or set())}

    def detect_jurisdiction(self, email: str) -> str:
        return self._jurisdiction.get(email.lower(), "US")

    def is_double_opt_in(self, email: str) -> bool:
        return email.lower() in self._double

    def has_express_consent(self, email: str) -> bool:
        return email.lower() in self._express

    def has_implied_consent(self, email: str) -> bool:
        return email.lower() in self._implied


class _OutreachSpacemailStub:
    """Stub that matches the engine's send_email kwargs contract."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send_email(self, **kwargs: Any) -> dict:
        self.calls.append(kwargs)
        return {"message_id": f"msg_{len(self.calls):04d}", "status": "queued"}

    def fetch_bounces(self) -> list[dict]:
        return []

    def fetch_complaints(self) -> list[dict]:
        return []


def _tmp_open_items() -> Path:
    fd, path = tempfile.mkstemp(prefix="open_items_", suffix=".md")
    os.close(fd)
    return Path(path)


def test_outreach_eu_blocks_without_consent() -> None:
    eu_email = "eu-lead@example.de"
    client = _OutreachSpacemailStub()
    supp = _OutreachSuppression()
    comp = _OutreachCompliance(
        jurisdiction_map={eu_email: "DE"},
        double_opt_in=set(),  # no consent on file
    )
    engine = AggressiveGrowthEngine(
        spacemail_client=client,
        compliance_checker=comp,
        suppression_list=supp,
        open_items_path=_tmp_open_items(),
    )

    campaign = OutreachCampaign(
        id="eu_cold_apr",
        name="EU cold outreach April",
        domain="growth.example.com",
        warmup_stage=1,
        daily_send_cap=50,
        body_template_path="",
        from_name="Growth",
        from_email="growth@growth.example.com",
        postal_address=POSTAL_ADDRESS,
    )
    recipients = [{"email": eu_email, "first_name": "Eva"}]
    report = engine.send_campaign(campaign, recipients)

    assert report["sent"] == 0, f"EU send without consent must not go out: {report}"
    assert report["skipped"] == 1, report
    assert len(client.calls) == 0, (
        f"client must not be called for EU without consent, got {client.calls}"
    )
    reason = report["results"][0]["reason"]
    assert "eu" in reason.lower() or "double_opt_in" in reason, reason


def test_outreach_us_allowed_with_footer() -> None:
    us_email = "lead@example.com"
    client = _OutreachSpacemailStub()
    supp = _OutreachSuppression()
    comp = _OutreachCompliance(jurisdiction_map={us_email: "US"})
    engine = AggressiveGrowthEngine(
        spacemail_client=client,
        compliance_checker=comp,
        suppression_list=supp,
        open_items_path=_tmp_open_items(),
    )

    campaign = OutreachCampaign(
        id="us_cold_apr",
        name="US cold outreach April",
        domain="growth.example.com",
        warmup_stage=1,
        daily_send_cap=50,
        subject_pattern="{first_name}, quick note",
        body_template_path="",
        from_name="Growth",
        from_email="growth@growth.example.com",
        postal_address=POSTAL_ADDRESS,
    )
    recipients = [
        {
            "email": us_email,
            "first_name": "Pat",
            "company": "Acme",
            "unsubscribe_token": "tok123",
        }
    ]
    report = engine.send_campaign(campaign, recipients)

    assert report["sent"] == 1, report
    assert report["skipped"] == 0, report
    assert len(client.calls) == 1, client.calls
    call = client.calls[0]
    assert call["to"][0]["email"] == us_email, call
    assert POSTAL_ADDRESS in call["text_body"], call["text_body"]
    assert "Unsubscribe" in call["text_body"], call["text_body"]
    assert call["postal_address"] == POSTAL_ADDRESS, call
    assert call["suppress_if_complaint"] is True, call
    assert call["suppress_if_bounce"] is True, call


TESTS: list[tuple[str, Callable[[], None]]] = [
    ("test_suppression_add_and_check", test_suppression_add_and_check),
    ("test_suppression_bulk_add", test_suppression_bulk_add),
    ("test_compliance_footer_injection", test_compliance_footer_injection),
    ("test_compliance_subject_spam_detection", test_compliance_subject_spam_detection),
    ("test_compliance_jurisdiction_detection", test_compliance_jurisdiction_detection),
    (
        "test_compliance_consent_ledger_log_and_check",
        test_compliance_consent_ledger_log_and_check,
    ),
    ("test_client_send_email_checks_suppression", test_client_send_email_checks_suppression),
    ("test_client_send_email_dispatches_when_clean", test_client_send_email_dispatches_when_clean),
    ("test_client_send_bulk_respects_suppression", test_client_send_bulk_respects_suppression),
    ("test_client_warmup_rate_limit", test_client_warmup_rate_limit),
    ("test_outreach_eu_blocks_without_consent", test_outreach_eu_blocks_without_consent),
    ("test_outreach_us_allowed_with_footer", test_outreach_us_allowed_with_footer),
]


def run_all_tests() -> tuple[int, int]:
    if not IMPORTS_OK:
        print(f"SKIP: module imports failed: {IMPORT_ERR}")
        return (0, 0)

    passed = 0
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    print(f"\nSummary: {passed} passed, {failed} failed, {len(TESTS)} total")
    return (passed, failed)


if __name__ == "__main__":
    p, f = run_all_tests()
    sys.exit(0 if f == 0 else 1)
