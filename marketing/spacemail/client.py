"""
SpacemailClient: the only sanctioned outbound email path.

Every outbound message in this repository must route through this
client. The client wraps the Spacemail Insight MCP tool surface
(tool names prefixed with mcp__claude_ai_Spacemail_Insight__) and
refuses to dispatch any message that:

  1. Targets a suppressed address (bounce, complaint, unsubscribe).
  2. Fails ComplianceChecker validation (CAN-SPAM, GDPR, CASL).
  3. Exceeds the warm up rate limit for a new sending domain.

Direct SMTP, SendGrid, Mailgun, SES, Postmark, Resend, and nodemailer
are all forbidden. See .claude/rules/13-spacemail-only.md for policy.

This module does not import any MCP client library. The MCP tool
dispatcher is injected as a callable in the constructor so that the
class is unit testable without a live MCP session.

All dashes in this file are ASCII hyphen minus (U+002D).
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Optional


MCP_TOOL_PREFIX = "mcp__claude_ai_Spacemail_Insight__"

# Warm up schedule for a freshly provisioned sending domain. The
# ceilings apply per rolling hour. The client refuses to send beyond
# the current day's ceiling until the next day begins.
WARMUP_SCHEDULE = [
    (1, 50),
    (2, 100),
    (3, 200),
    (4, 350),
    (5, 500),
    (6, 500),
    (7, 500),
]
MAX_HOURLY_CEILING = 500
WARMUP_DAYS = len(WARMUP_SCHEDULE)


def _default_log_path() -> str:
    return str(Path("~/.opencode/spacemail.log").expanduser())


def _configure_logger(log_path: str) -> logging.Logger:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("spacemail.client")
    if not logger.handlers:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class SpacemailClient:
    """Sanctioned outbound email client."""

    def __init__(
        self,
        suppression,
        compliance,
        mcp_dispatcher: Optional[Callable[[str, dict], dict]] = None,
        mcp_prefix: str = MCP_TOOL_PREFIX,
        domain_started_ts: Optional[int] = None,
        log_path: Optional[str] = None,
    ) -> None:
        """
        suppression: SuppressionList instance from suppression.py
        compliance: ComplianceChecker instance from compliance.py
        mcp_dispatcher: optional callable(tool_name, args) -> result.
            When None, a stub that raises RuntimeError is used; the
            runtime must supply a real dispatcher bound to the MCP
            session.
        mcp_prefix: tool namespace, defaults to the Spacemail Insight
            MCP prefix. Do not change unless the MCP surface is renamed.
        domain_started_ts: Unix timestamp when the sending domain was
            provisioned. Used to compute the warm up day.
        log_path: path to the log file. Defaults to ~/.opencode/spacemail.log.
        """
        self.suppression = suppression
        self.compliance = compliance
        self.mcp_prefix = mcp_prefix
        self._dispatcher = mcp_dispatcher or self._no_dispatcher
        self.domain_started_ts = domain_started_ts or int(time.time())
        self.log_path = log_path or _default_log_path()
        self.logger = _configure_logger(self.log_path)
        # Rolling timestamps of sends for rate limiting.
        self._send_history: deque[float] = deque()

    @staticmethod
    def _no_dispatcher(tool: str, args: dict) -> dict:
        raise RuntimeError(
            f"no MCP dispatcher configured; cannot invoke {tool}. "
            "Bind a real mcp_dispatcher before sending."
        )

    def _dispatch(self, tool: str, args: dict) -> dict:
        """Invoke a Spacemail Insight MCP tool by its short name."""
        full = f"{self.mcp_prefix}{tool}"
        self.logger.info("dispatch tool=%s", full)
        return self._dispatcher(full, args)

    def _current_warmup_ceiling(self) -> int:
        """Return the hourly send ceiling for the current warm up day."""
        age_seconds = max(0, int(time.time()) - self.domain_started_ts)
        age_days = age_seconds // 86400 + 1
        if age_days >= WARMUP_DAYS:
            return MAX_HOURLY_CEILING
        for day, ceiling in WARMUP_SCHEDULE:
            if age_days <= day:
                return ceiling
        return MAX_HOURLY_CEILING

    def _prune_rate_window(self) -> None:
        cutoff = time.time() - 3600
        while self._send_history and self._send_history[0] < cutoff:
            self._send_history.popleft()

    def _rate_limit_check(self) -> None:
        self._prune_rate_window()
        ceiling = self._current_warmup_ceiling()
        if len(self._send_history) >= ceiling:
            raise RuntimeError(
                f"warm up rate limit reached: "
                f"{len(self._send_history)} of {ceiling} per hour"
            )

    def _record_send(self) -> None:
        self._send_history.append(time.time())

    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_name: str,
        from_email: str,
        reply_to: Optional[str] = None,
        tags: Optional[list[str]] = None,
        unsubscribe_url: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        inject_footer: bool = True,
    ) -> dict:
        """
        Send a single email through the Spacemail Insight MCP surface.
        Returns the MCP result dict (expected to contain a message_id).
        """
        # Suppression check.
        suppressed, reason = self.suppression.is_suppressed(to)
        if suppressed:
            self.logger.warning(
                "blocked send to %s, suppression reason: %s", to, reason
            )
            return {
                "status": "blocked",
                "reason": f"suppressed: {reason}",
                "to": to,
            }

        # Footer injection.
        html = body_html
        text = body_text
        if inject_footer:
            if not unsubscribe_url:
                raise ValueError(
                    "unsubscribe_url is required when inject_footer is True"
                )
            html, text = self.compliance.inject_footer(
                html, text, unsubscribe_url
            )

        # Compliance validation on the final rendered body.
        ok, issues = self.compliance.validate_outbound(
            to, subject, text, jurisdiction=jurisdiction
        )
        if not ok:
            self.logger.warning(
                "blocked send to %s, compliance issues: %s", to, issues
            )
            return {
                "status": "blocked",
                "reason": "compliance",
                "issues": issues,
                "to": to,
            }

        # Rate limiter.
        self._rate_limit_check()

        args = {
            "to": to,
            "subject": subject,
            "body_html": html,
            "body_text": text,
            "from_name": from_name,
            "from_email": from_email,
        }
        if reply_to:
            args["reply_to"] = reply_to
        if tags:
            args["tags"] = list(tags)
        if unsubscribe_url:
            args["headers"] = {
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }

        result = self._dispatch("send_email", args)
        self._record_send()
        self.logger.info(
            "sent to=%s subject=%r message_id=%s",
            to, subject, result.get("message_id", "unknown"),
        )
        return result

    def send_bulk(
        self,
        recipients: list[dict],
        subject: str,
        body_html: str,
        body_text: str,
        from_name: str,
        from_email: str,
        unsubscribe_url_template: str,
        delay_ms: int = 100,
        reply_to: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> dict:
        """
        Send the same message to a list of recipients with throttling.

        recipients: list of dicts, each with keys 'email' and optional
            'first_name', 'unsubscribe_token'. The token is substituted
            into unsubscribe_url_template via {{token}}.
        delay_ms: inter send delay in milliseconds.

        Returns aggregate counts: {sent, blocked, failed, total}.
        """
        sent = 0
        blocked = 0
        failed = 0
        details: list[dict] = []

        for rcpt in recipients:
            email = rcpt["email"]
            token = rcpt.get("unsubscribe_token", "")
            personalized_html = body_html.replace(
                "{{first_name}}", rcpt.get("first_name", "there")
            )
            personalized_text = body_text.replace(
                "{{first_name}}", rcpt.get("first_name", "there")
            )
            unsub_url = unsubscribe_url_template.replace("{{token}}", token)

            try:
                result = self.send_email(
                    to=email,
                    subject=subject,
                    body_html=personalized_html,
                    body_text=personalized_text,
                    from_name=from_name,
                    from_email=from_email,
                    reply_to=reply_to,
                    tags=tags,
                    unsubscribe_url=unsub_url,
                )
                status = result.get("status", "sent")
                if status == "blocked":
                    blocked += 1
                else:
                    sent += 1
                details.append({"email": email, "status": status})
            except Exception as exc:
                failed += 1
                self.logger.exception(
                    "send_bulk failed for %s: %s", email, exc
                )
                details.append(
                    {"email": email, "status": "failed", "error": str(exc)}
                )

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

        return {
            "sent": sent,
            "blocked": blocked,
            "failed": failed,
            "total": len(recipients),
            "details": details,
        }

    def search_messages(self, query: str, limit: int = 50) -> list[dict]:
        """Search the mailbox via the MCP search_messages tool."""
        result = self._dispatch(
            "search_messages", {"query": query, "limit": limit}
        )
        if isinstance(result, dict):
            return list(result.get("messages", []))
        if isinstance(result, list):
            return result
        return []

    def create_draft(self, to: str, subject: str, body: str) -> dict:
        """Create a draft message without sending."""
        return self._dispatch(
            "create_draft",
            {"to": to, "subject": subject, "body": body},
        )

    def get_message(self, message_id: str) -> dict:
        """Fetch a single message by id."""
        return self._dispatch("get_message", {"message_id": message_id})

    def mark_read(self, message_id: str) -> dict:
        """Mark a message as read."""
        return self._dispatch("mark_read", {"message_id": message_id})

    def fetch_bounces(self, since_ts: Optional[int] = None) -> list[dict]:
        """Fetch recent bounce events from the MCP surface."""
        args: dict = {}
        if since_ts is not None:
            args["since"] = since_ts
        result = self._dispatch("fetch_bounces", args)
        if isinstance(result, dict):
            return list(result.get("bounces", []))
        if isinstance(result, list):
            return result
        return []

    def fetch_complaints(self, since_ts: Optional[int] = None) -> list[dict]:
        """Fetch recent complaint events from the MCP surface."""
        args: dict = {}
        if since_ts is not None:
            args["since"] = since_ts
        result = self._dispatch("fetch_complaints", args)
        if isinstance(result, dict):
            return list(result.get("complaints", []))
        if isinstance(result, list):
            return result
        return []

    def sync_suppressions(self) -> dict:
        """
        Poll the MCP surface for new bounces and complaints, then insert
        them into the local SuppressionList. Returns counts of added
        entries per category.
        """
        added = {"bounce_hard": 0, "bounce_soft": 0, "complaint": 0}

        for bounce in self.fetch_bounces():
            email = bounce.get("email")
            if not email:
                continue
            hard = bool(bounce.get("hard")) or bounce.get("type") == "hard"
            category = "bounce_hard" if hard else "bounce_soft"
            reason = bounce.get("reason") or bounce.get("diagnostic", "bounce")
            self.suppression.add(
                email, reason, category, source="spacemail.bounces"
            )
            added[category] += 1

        for complaint in self.fetch_complaints():
            email = complaint.get("email")
            if not email:
                continue
            reason = complaint.get("reason") or "recipient marked as spam"
            self.suppression.add(
                email, reason, "complaint", source="spacemail.complaints"
            )
            added["complaint"] += 1

        self.logger.info("sync_suppressions added=%s", added)
        return added
