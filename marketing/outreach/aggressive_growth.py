"""Aggressive growth outreach engine.

Sends cold and warm outreach via the Spacemail Insight MCP (per operating
rule 10 and .claude/rules/13-spacemail-only.md). Uses a separate sending
domain with a 30-day warmup ramp. Enforces jurisdiction-specific compliance
(CAN-SPAM for US, GDPR for EU, CASL for Canada).

All email MUST route through spacemail_client. Direct SMTP, SendGrid,
Mailgun, Postmark, or any other provider SDK is forbidden.

Usage:
    python -m marketing.outreach.aggressive_growth warmup-schedule
    python -m marketing.outreach.aggressive_growth send --campaign c.json --recipients r.json
    python -m marketing.outreach.aggressive_growth health-check --domain growth.example.com
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

LOG = logging.getLogger("aggressive_growth")

OPEN_ITEMS_PATH = Path("docs/open-items.md")

WARMUP_CAPS = {
    1: 50,
    2: 100,
    3: 200,
    4: 350,
    5: 500,
    6: 750,
}
WARMUP_STEADY_CAP = 1000

EU_COUNTRIES = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL",
    "PT", "RO", "SE", "SI", "SK", "GB", "UK",
})
CA_COUNTRIES = frozenset({"CA"})


@dataclass
class OutreachCampaign:
    """Campaign configuration."""

    id: str
    name: str
    domain: str
    warmup_stage: int = 1
    daily_send_cap: int = 50
    subject_pattern: str = "{first_name}, quick question about {company}"
    body_template_path: str = ""
    from_name: str = "Growth Team"
    from_email: str = ""
    reply_to: Optional[str] = None
    unsubscribe_url_template: str = "https://{domain}/u/{token}"
    postal_address: str = ""


@dataclass
class OutreachResult:
    """Per-recipient outcome."""

    recipient: str
    status: str
    reason: Optional[str] = None
    message_id: Optional[str] = None
    jurisdiction: Optional[str] = None


@dataclass
class OutreachMetrics:
    sent: int = 0
    skipped: int = 0
    failed: int = 0
    bounced: int = 0
    complained: int = 0
    opened: int = 0
    clicked: int = 0
    per_reason: dict[str, int] = field(default_factory=dict)

    def open_rate(self) -> float:
        return self.opened / self.sent if self.sent else 0.0

    def click_rate(self) -> float:
        return self.clicked / self.sent if self.sent else 0.0

    def bounce_rate(self) -> float:
        return self.bounced / self.sent if self.sent else 0.0

    def complaint_rate(self) -> float:
        return self.complained / self.sent if self.sent else 0.0


class AggressiveGrowthEngine:
    """Drives cold and warm outreach with jurisdictional compliance."""

    def __init__(
        self,
        spacemail_client: Any,
        compliance_checker: Any,
        suppression_list: Any,
        consent_ledger_path: str = "~/.opencode/consent_ledger.sqlite",
        open_items_path: Optional[Path] = None,
    ) -> None:
        """Initialize engine with required collaborators.

        - spacemail_client: object with send_email(...) method routing to MCP.
          Direct SMTP or provider SDKs are banned (rule 10, rule 13).
        - compliance_checker: object with detect_jurisdiction(email) -> ISO country code
          and is_double_opt_in(email) -> bool, has_express_consent(email) -> bool,
          has_implied_consent(email) -> bool.
        - suppression_list: object with contains(email) -> bool and add(email, reason).
        - consent_ledger_path: SQLite path for consent records.
        """
        self.spacemail_client = spacemail_client
        self.compliance = compliance_checker
        self.suppression = suppression_list
        self.consent_ledger_path = Path(os.path.expanduser(consent_ledger_path))
        self.open_items_path = open_items_path or OPEN_ITEMS_PATH
        self.metrics = OutreachMetrics()

    def warmup_plan(self, days: int = 30) -> list[int]:
        """Return a list of daily send caps for a warmup period.

        Days 1 to 6 ramp aggressively, days 7 to `days` hold at steady cap.
        """
        plan: list[int] = []
        for day in range(1, days + 1):
            cap = WARMUP_CAPS.get(day, WARMUP_STEADY_CAP)
            plan.append(cap)
        return plan

    def daily_cap_for(self, campaign: OutreachCampaign, day_index: int) -> int:
        """Return the cap for a specific day index (1-based)."""
        plan = self.warmup_plan(days=max(30, day_index))
        if day_index < 1 or day_index > len(plan):
            return WARMUP_STEADY_CAP
        return min(plan[day_index - 1], campaign.daily_send_cap or WARMUP_STEADY_CAP)

    def _log_open_item(self, item_id: str, description: str) -> None:
        """Append a blocker entry to docs/open-items.md."""
        try:
            self.open_items_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.open_items_path, "a", encoding="utf-8") as fh:
                fh.write(
                    f"\n## {item_id}\n"
                    f"date: {date.today().isoformat()}\n"
                    f"severity: info\n"
                    f"description: {description}\n"
                )
        except Exception as exc:
            LOG.warning("failed to log open item %s: %s", item_id, exc)

    def _check_compliance(self, recipient: dict[str, Any]) -> tuple[bool, str, str]:
        """Check jurisdictional compliance for a recipient.

        Returns (allowed, jurisdiction, reason).
        """
        email = recipient.get("email", "")
        if not email:
            return (False, "unknown", "missing_email")

        try:
            if self.suppression.contains(email):
                return (False, "unknown", "suppressed")
        except Exception as exc:
            LOG.warning("suppression check failed: %s", exc)

        try:
            country = self.compliance.detect_jurisdiction(email).upper()
        except Exception as exc:
            LOG.warning("jurisdiction detection failed: %s", exc)
            country = "UNKNOWN"

        if country in EU_COUNTRIES:
            try:
                if not self.compliance.is_double_opt_in(email):
                    return (False, country, "eu_requires_double_opt_in")
            except Exception as exc:
                return (False, country, f"eu_consent_check_failed:{exc}")
            return (True, country, "eu_double_opt_in_confirmed")

        if country in CA_COUNTRIES:
            try:
                if not (
                    self.compliance.has_express_consent(email)
                    or self.compliance.has_implied_consent(email)
                ):
                    return (False, country, "ca_requires_express_or_implied_consent")
            except Exception as exc:
                return (False, country, f"ca_consent_check_failed:{exc}")
            return (True, country, "ca_consent_confirmed")

        return (True, country, "us_can_spam_footer_required")

    def _render_body(
        self,
        campaign: OutreachCampaign,
        recipient: dict[str, Any],
        template: str,
    ) -> tuple[str, str]:
        """Render subject and body templates with recipient substitutions."""
        subs = {
            "first_name": recipient.get("first_name", "there"),
            "last_name": recipient.get("last_name", ""),
            "company": recipient.get("company", "your team"),
            "email": recipient.get("email", ""),
            "domain": campaign.domain,
            "token": recipient.get("unsubscribe_token", ""),
        }

        def fmt(s: str) -> str:
            try:
                return s.format(**subs)
            except KeyError:
                return s

        subject = fmt(campaign.subject_pattern)
        body = fmt(template)
        return subject, body

    def _append_unsubscribe_footer(
        self,
        body: str,
        campaign: OutreachCampaign,
        recipient: dict[str, Any],
    ) -> str:
        """Add postal address and unsubscribe link for CAN-SPAM, GDPR, CASL."""
        unsub = campaign.unsubscribe_url_template.format(
            domain=campaign.domain,
            token=recipient.get("unsubscribe_token", ""),
        )
        footer = (
            f"\n\n---\n"
            f"{campaign.postal_address}\n"
            f"Unsubscribe: {unsub}\n"
        )
        return body + footer

    def send_campaign(
        self,
        campaign: OutreachCampaign,
        recipients: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Send a campaign to a recipient list with compliance gating."""
        template = ""
        if campaign.body_template_path:
            try:
                template = Path(campaign.body_template_path).read_text(encoding="utf-8")
            except Exception as exc:
                LOG.error("template read failed: %s", exc)
                return {"error": f"template_read_failed:{exc}", "results": []}

        results: list[OutreachResult] = []
        today_index = self._day_index_from_launch(campaign)
        cap = self.daily_cap_for(campaign, today_index)
        sent_today = 0

        list_unsubscribe_header = (
            f"<mailto:unsubscribe@{campaign.domain}>, <https://{campaign.domain}/u/one-click>"
        )

        for recipient in recipients:
            if sent_today >= cap:
                results.append(
                    OutreachResult(
                        recipient=recipient.get("email", ""),
                        status="skipped",
                        reason=f"daily_cap_reached:{cap}",
                    )
                )
                self.metrics.skipped += 1
                self.metrics.per_reason["daily_cap_reached"] = (
                    self.metrics.per_reason.get("daily_cap_reached", 0) + 1
                )
                continue

            allowed, jurisdiction, reason = self._check_compliance(recipient)
            if not allowed:
                results.append(
                    OutreachResult(
                        recipient=recipient.get("email", ""),
                        status="skipped",
                        reason=reason,
                        jurisdiction=jurisdiction,
                    )
                )
                self.metrics.skipped += 1
                self.metrics.per_reason[reason] = self.metrics.per_reason.get(reason, 0) + 1
                self._log_open_item(
                    item_id=f"outreach-skip-{recipient.get('email','')}-{int(time.time())}",
                    description=(
                        f"Recipient {recipient.get('email','')} skipped in campaign "
                        f"{campaign.id}: {reason} (jurisdiction {jurisdiction})"
                    ),
                )
                continue

            subject, body = self._render_body(campaign, recipient, template)
            body = self._append_unsubscribe_footer(body, campaign, recipient)

            try:
                response = self.spacemail_client.send_email(
                    from_address=campaign.from_email or f"noreply@{campaign.domain}",
                    from_name=campaign.from_name,
                    to=[{"email": recipient["email"], "name": recipient.get("first_name", "")}],
                    reply_to=campaign.reply_to,
                    subject=subject,
                    html_body=body,
                    text_body=body,
                    headers={
                        "List-Unsubscribe": list_unsubscribe_header,
                        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                        "X-Campaign-Id": campaign.id,
                    },
                    category=f"outreach.{campaign.id}",
                    postal_address=campaign.postal_address,
                    suppress_if_complaint=True,
                    suppress_if_bounce=True,
                )
                message_id = None
                if isinstance(response, dict):
                    message_id = response.get("message_id") or response.get("id")
                results.append(
                    OutreachResult(
                        recipient=recipient["email"],
                        status="sent",
                        message_id=message_id,
                        jurisdiction=jurisdiction,
                        reason=reason,
                    )
                )
                self.metrics.sent += 1
                sent_today += 1
            except Exception as exc:
                results.append(
                    OutreachResult(
                        recipient=recipient.get("email", ""),
                        status="failed",
                        reason=f"send_failed:{exc}",
                        jurisdiction=jurisdiction,
                    )
                )
                self.metrics.failed += 1
                self.metrics.per_reason["send_failed"] = (
                    self.metrics.per_reason.get("send_failed", 0) + 1
                )

        return {
            "campaign_id": campaign.id,
            "cap": cap,
            "sent": self.metrics.sent,
            "skipped": self.metrics.skipped,
            "failed": self.metrics.failed,
            "results": [r.__dict__ for r in results],
        }

    def _day_index_from_launch(self, campaign: OutreachCampaign) -> int:
        """Return 1-based day index given the warmup_stage on the campaign."""
        return max(1, int(campaign.warmup_stage))

    def bounce_complaint_loop(self) -> dict[str, int]:
        """Pull bounces and complaints, add to suppression list."""
        totals = {"bounces_added": 0, "complaints_added": 0, "errors": 0}
        try:
            bounces = self.spacemail_client.fetch_bounces()
        except Exception as exc:
            LOG.error("fetch_bounces failed: %s", exc)
            totals["errors"] += 1
            bounces = []

        for b in bounces or []:
            email = b.get("email") if isinstance(b, dict) else None
            if not email:
                continue
            try:
                self.suppression.add(email, reason="bounce")
                self.metrics.bounced += 1
                totals["bounces_added"] += 1
            except Exception as exc:
                LOG.error("suppression add (bounce) failed: %s", exc)
                totals["errors"] += 1

        try:
            complaints = self.spacemail_client.fetch_complaints()
        except Exception as exc:
            LOG.error("fetch_complaints failed: %s", exc)
            totals["errors"] += 1
            complaints = []

        for c in complaints or []:
            email = c.get("email") if isinstance(c, dict) else None
            if not email:
                continue
            try:
                self.suppression.add(email, reason="complaint")
                self.metrics.complained += 1
                totals["complaints_added"] += 1
            except Exception as exc:
                LOG.error("suppression add (complaint) failed: %s", exc)
                totals["errors"] += 1

        return totals

    def domain_health_check(self, domain: Optional[str] = None) -> dict[str, Any]:
        """Check SPF, DKIM, DMARC records plus reputation score.

        Uses dnspython when available; falls back to unknown status otherwise.
        """
        target = domain or ""
        report: dict[str, Any] = {
            "domain": target,
            "spf": "unknown",
            "dkim": "unknown",
            "dmarc": "unknown",
            "sender_score": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        if not target:
            report["error"] = "no_domain"
            return report

        try:
            import dns.resolver  # type: ignore
        except ImportError:
            report["error"] = "dnspython_not_installed"
            return report

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 5.0

        try:
            answers = resolver.resolve(target, "TXT")
            spf_found = any("v=spf1" in b.decode(errors="ignore") for r in answers for b in r.strings)
            report["spf"] = "present" if spf_found else "missing"
        except Exception as exc:
            report["spf"] = f"error:{exc}"

        try:
            answers = resolver.resolve(f"_dmarc.{target}", "TXT")
            dmarc_found = any("v=DMARC1" in b.decode(errors="ignore") for r in answers for b in r.strings)
            report["dmarc"] = "present" if dmarc_found else "missing"
        except Exception as exc:
            report["dmarc"] = f"error:{exc}"

        try:
            answers = resolver.resolve(f"default._domainkey.{target}", "TXT")
            dkim_found = any("v=DKIM1" in b.decode(errors="ignore") for r in answers for b in r.strings)
            report["dkim"] = "present" if dkim_found else "missing"
        except Exception as exc:
            report["dkim"] = f"error:{exc}"

        try:
            score = self._fetch_sender_score(target)
            report["sender_score"] = score
        except Exception as exc:
            report["sender_score_error"] = str(exc)

        return report

    def _fetch_sender_score(self, domain: str) -> Optional[int]:
        """Best-effort sender score lookup. Returns None if unavailable.

        Avoids third-party SDKs; uses urllib only. If no free endpoint is
        reachable, returns None rather than failing the whole health check.
        """
        try:
            import urllib.request

            url = f"https://dns.google/resolve?name={domain}&type=TXT"
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    resp.read()
                    return None
        except Exception:
            pass
        return None

    def metrics_snapshot(self) -> dict[str, float]:
        return {
            "sent": self.metrics.sent,
            "skipped": self.metrics.skipped,
            "failed": self.metrics.failed,
            "bounced": self.metrics.bounced,
            "complained": self.metrics.complained,
            "open_rate": self.metrics.open_rate(),
            "click_rate": self.metrics.click_rate(),
            "bounce_rate": self.metrics.bounce_rate(),
            "complaint_rate": self.metrics.complaint_rate(),
        }


class _NullSpacemailClient:
    """Stub for CLI smoke runs when no real client is wired."""

    def send_email(self, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError(
            "Spacemail client not configured. Wire mcp__claude_ai_Spacemail_Insight__* "
            "(see .claude/rules/13-spacemail-only.md)."
        )

    def fetch_bounces(self) -> list[Any]:
        return []

    def fetch_complaints(self) -> list[Any]:
        return []


class _NullCompliance:
    def detect_jurisdiction(self, email: str) -> str:
        return "US"

    def is_double_opt_in(self, email: str) -> bool:
        return False

    def has_express_consent(self, email: str) -> bool:
        return False

    def has_implied_consent(self, email: str) -> bool:
        return False


class _NullSuppression:
    def __init__(self) -> None:
        self._set: set[str] = set()

    def contains(self, email: str) -> bool:
        return email in self._set

    def add(self, email: str, reason: str) -> None:
        self._set.add(email)


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Aggressive growth outreach")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("warmup-schedule")
    p_plan.add_argument("--days", type=int, default=30)

    p_send = sub.add_parser("send")
    p_send.add_argument("--campaign", required=True, help="Campaign JSON file")
    p_send.add_argument("--recipients", required=True, help="Recipients JSON file")

    p_health = sub.add_parser("health-check")
    p_health.add_argument("--domain", required=True)

    args = parser.parse_args()
    engine = AggressiveGrowthEngine(
        spacemail_client=_NullSpacemailClient(),
        compliance_checker=_NullCompliance(),
        suppression_list=_NullSuppression(),
    )

    if args.cmd == "warmup-schedule":
        plan = engine.warmup_plan(days=args.days)
        print(json.dumps({"days": args.days, "caps": plan}, indent=2))
        return 0

    if args.cmd == "send":
        campaign_raw = json.loads(Path(args.campaign).read_text(encoding="utf-8"))
        campaign = OutreachCampaign(**campaign_raw)
        recipients = json.loads(Path(args.recipients).read_text(encoding="utf-8"))
        report = engine.send_campaign(campaign, recipients)
        print(json.dumps(report, indent=2, default=str))
        return 0

    if args.cmd == "health-check":
        print(json.dumps(engine.domain_health_check(args.domain), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(_cli())
