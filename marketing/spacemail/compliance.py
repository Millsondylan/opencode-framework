"""
Outbound email compliance checks: CAN-SPAM, GDPR, CASL.

ComplianceChecker validates every outbound message against the union of
three jurisdictions:

  CAN-SPAM (United States)
    1. Accurate from/reply-to headers.
    2. No deceptive subject line.
    3. Physical postal address in footer.
    4. Working unsubscribe link.

  GDPR (European Union)
    1. Lawful basis, typically double opt in consent.
    2. Consent ledger with timestamp, method, source.
    3. Easy withdrawal, one click unsubscribe.

  CASL (Canada)
    1. Express or implied consent on file.
    2. Sender identification, postal address.
    3. Working unsubscribe mechanism.

The checker does not send mail. It validates a payload and optionally
injects the compliance footer. Actual dispatch is handled by the
SpacemailClient in client.py.

All dashes in this file are ASCII hyphen minus (U+002D).
"""

from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path
from typing import Optional


# TLD based jurisdiction detection. Not authoritative: the recipient may
# be an EU citizen using a .com address. When in doubt, the caller should
# pass jurisdiction explicitly.
EU_TLDS = {
    "eu", "de", "fr", "it", "es", "nl", "be", "at", "dk", "se", "fi",
    "pt", "ie", "gr", "cz", "pl", "hu", "ro", "bg", "sk", "si", "hr",
    "lt", "lv", "ee", "lu", "mt", "cy",
}
UK_TLDS = {"uk", "co.uk"}
CA_TLDS = {"ca"}
US_TLDS = {"us", "com", "org", "net", "gov", "edu", "mil"}

# Subject line patterns that commonly trigger spam filters. A hit does
# not always mean the subject is bad, but every hit should be reviewed.
SUBJECT_SPAM_PATTERNS = [
    (re.compile(r"^[A-Z0-9 !?,.]{15,}$"), "subject is all caps"),
    (re.compile(r"[!?]{2,}"), "excessive punctuation"),
    (re.compile(r"\$\$+"), "multiple dollar signs"),
    (re.compile(r"\b(free|winner|urgent|act now|limited time)\b", re.I),
     "spam trigger word"),
    (re.compile(r"100%\s*(free|guaranteed)", re.I), "100 percent claim"),
    (re.compile(r"click here", re.I), "vague link text"),
    (re.compile(r"\bRe:\s*$", re.I), "fake reply prefix"),
]

# Matches a simple "City, Region, Postal, Country" shape.
POSTAL_ADDRESS_PATTERN = re.compile(
    r".+,\s*.+,\s*.+,\s*.+"
)


class ComplianceChecker:
    """Validates outbound email against CAN-SPAM, GDPR, and CASL."""

    def __init__(
        self,
        postal_address: str,
        company_name: str,
        consent_ledger_path: str = "~/.opencode/consent_ledger.sqlite",
    ) -> None:
        if not POSTAL_ADDRESS_PATTERN.match(postal_address.strip()):
            raise ValueError(
                "postal_address must be in the format "
                "'Company, Street, City, Region Postal, Country'"
            )
        self.postal_address = postal_address.strip()
        self.company_name = company_name.strip()
        self.consent_ledger_path = str(Path(consent_ledger_path).expanduser())
        Path(self.consent_ledger_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_ledger()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.consent_ledger_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_ledger(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    jurisdiction TEXT NOT NULL,
                    method TEXT NOT NULL,
                    source TEXT,
                    ip TEXT,
                    confirmed_ts INTEGER,
                    recorded_ts INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_consent_email "
                "ON consent(email)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_consent_jurisdiction "
                "ON consent(jurisdiction)"
            )

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def detect_jurisdiction(self, email_or_domain: str) -> str:
        """Rough TLD based jurisdiction guess. Returns 'eu', 'ca', 'us', 'other'."""
        target = email_or_domain.strip().lower()
        if "@" in target:
            target = target.split("@", 1)[1]
        if not target:
            return "other"
        parts = target.split(".")
        if len(parts) >= 2 and f"{parts[-2]}.{parts[-1]}" in UK_TLDS:
            return "eu"
        tld = parts[-1]
        if tld in EU_TLDS or tld in UK_TLDS:
            return "eu"
        if tld in CA_TLDS:
            return "ca"
        if tld in US_TLDS:
            return "us"
        return "other"

    def validate_outbound(
        self,
        recipient: str,
        subject: str,
        body: str,
        jurisdiction: Optional[str] = None,
    ) -> tuple[bool, list[str]]:
        """
        Run every compliance check on a candidate message.
        Returns (ok, issues). When issues is non empty, do not send.
        """
        issues: list[str] = []

        if jurisdiction is None:
            jurisdiction = self.detect_jurisdiction(recipient)

        # Subject line checks.
        subject_stripped = subject.strip()
        if not subject_stripped:
            issues.append("subject line is empty")
        if len(subject_stripped) > 78:
            issues.append("subject line exceeds 78 characters, may truncate")
        for pattern, label in SUBJECT_SPAM_PATTERNS:
            if pattern.search(subject_stripped):
                issues.append(f"subject spam risk: {label}")

        # Body checks.
        body_lower = body.lower()
        if "unsubscribe" not in body_lower:
            issues.append("body is missing unsubscribe reference")
        if self.postal_address.lower() not in body_lower:
            issues.append(
                "body is missing physical postal address required by CAN-SPAM"
            )
        if self.company_name.lower() not in body_lower:
            issues.append("body is missing sender identification")

        # Jurisdiction specific checks.
        if jurisdiction in ("eu", "ca"):
            if not self.check_consent(recipient, jurisdiction):
                issues.append(
                    f"no valid consent on file for {jurisdiction} recipient"
                )

        # List unsubscribe hint. Not fatal but strongly recommended.
        if "list-unsubscribe" not in body_lower and "{{unsubscribe_url}}" not in body:
            issues.append(
                "recommend including List-Unsubscribe one click header"
            )

        return (len(issues) == 0, issues)

    def inject_footer(
        self,
        body_html: str,
        body_text: str,
        unsubscribe_url: str,
    ) -> tuple[str, str]:
        """Append CAN-SPAM footer to both HTML and plain text bodies."""
        if not unsubscribe_url:
            raise ValueError("unsubscribe_url is required")

        html_footer = (
            '\n<hr style="margin-top:32px;border:none;border-top:1px solid #ccc;">\n'
            '<div style="font-size:12px;color:#666;margin-top:12px;">\n'
            f'  <p>{self.company_name}<br>{self.postal_address}</p>\n'
            '  <p>'
            f'You received this email because you subscribed to updates from '
            f'{self.company_name}. '
            f'<a href="{unsubscribe_url}">Unsubscribe</a> '
            'or manage your preferences at any time.'
            '</p>\n'
            '</div>\n'
        )

        text_footer = (
            "\n\n"
            "----\n"
            f"{self.company_name}\n"
            f"{self.postal_address}\n\n"
            f"You received this email because you subscribed to updates "
            f"from {self.company_name}. "
            f"To unsubscribe, visit: {unsubscribe_url}\n"
        )

        return (body_html + html_footer, body_text + text_footer)

    def check_consent(self, email: str, jurisdiction: str) -> bool:
        """
        Return True when a valid consent record exists.
        For EU jurisdictions a confirmed double opt in is required.
        For CA (CASL) either express or implied consent is accepted.
        """
        norm = self._normalize_email(email)
        with self._connect() as conn:
            if jurisdiction == "eu":
                row = conn.execute(
                    """
                    SELECT 1 FROM consent
                    WHERE email = ?
                      AND jurisdiction = 'eu'
                      AND method = 'double_opt_in'
                      AND confirmed_ts IS NOT NULL
                    LIMIT 1
                    """,
                    (norm,),
                ).fetchone()
                return row is not None
            if jurisdiction == "ca":
                row = conn.execute(
                    """
                    SELECT 1 FROM consent
                    WHERE email = ?
                      AND jurisdiction = 'ca'
                      AND method IN ('express', 'implied', 'double_opt_in')
                    LIMIT 1
                    """,
                    (norm,),
                ).fetchone()
                return row is not None
            # Default: any consent record counts.
            row = conn.execute(
                "SELECT 1 FROM consent WHERE email = ? LIMIT 1",
                (norm,),
            ).fetchone()
            return row is not None

    def log_consent(
        self,
        email: str,
        jurisdiction: str,
        method: str,
        source: str,
        ip: Optional[str] = None,
        confirmed: bool = False,
    ) -> int:
        """
        Append a consent ledger entry.
        method: express | implied | double_opt_in | single_opt_in
        confirmed: True when the second click confirmation is done.
        """
        valid_methods = {"express", "implied", "double_opt_in", "single_opt_in"}
        if method not in valid_methods:
            raise ValueError(
                f"method must be one of {sorted(valid_methods)}, got {method!r}"
            )
        now = int(time.time())
        confirmed_ts = now if confirmed else None
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO consent
                    (email, jurisdiction, method, source, ip,
                     confirmed_ts, recorded_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._normalize_email(email),
                    jurisdiction,
                    method,
                    source,
                    ip,
                    confirmed_ts,
                    now,
                ),
            )
            return int(cur.lastrowid or 0)

    def confirm_consent(self, email: str, jurisdiction: str) -> bool:
        """Mark the most recent double opt in record as confirmed."""
        now = int(time.time())
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE consent
                SET confirmed_ts = ?
                WHERE id = (
                    SELECT id FROM consent
                    WHERE email = ? AND jurisdiction = ?
                      AND method = 'double_opt_in'
                      AND confirmed_ts IS NULL
                    ORDER BY recorded_ts DESC
                    LIMIT 1
                )
                """,
                (now, self._normalize_email(email), jurisdiction),
            )
            return cur.rowcount > 0

    def withdraw_consent(self, email: str) -> int:
        """Delete all consent records for an address (GDPR erasure)."""
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM consent WHERE email = ?",
                (self._normalize_email(email),),
            )
            return cur.rowcount
