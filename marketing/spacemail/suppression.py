"""
Suppression list manager for outbound email.

Tracks bounces, complaints, unsubscribes, and manual entries in a local
SQLite store. Soft bounces auto expire after 30 days. Hard bounces,
complaints, and unsubscribes are permanent unless explicitly removed.

Categories:
  bounce_hard  : permanent failure, never retry
  bounce_soft  : temporary failure, auto expire after 30 days
  complaint    : recipient marked as spam, permanent
  unsubscribe  : recipient requested opt out, permanent
  manual       : operator added entry, permanent

All dashes in this file are ASCII hyphen minus (U+002D) per rule 08.
"""

from __future__ import annotations

import csv
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional


SOFT_BOUNCE_EXPIRY_DAYS = 30
SECONDS_PER_DAY = 86400
VALID_CATEGORIES = {
    "bounce_hard",
    "bounce_soft",
    "complaint",
    "unsubscribe",
    "manual",
}


class SuppressionList:
    """Local SQLite backed suppression list."""

    def __init__(self, db_path: str = "~/.opencode/suppression.sqlite") -> None:
        self.db_path = str(Path(db_path).expanduser())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS suppressions (
                    email TEXT PRIMARY KEY,
                    reason TEXT NOT NULL,
                    category TEXT NOT NULL,
                    added_ts INTEGER NOT NULL,
                    source TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_suppressions_category "
                "ON suppressions(category)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_suppressions_added_ts "
                "ON suppressions(added_ts)"
            )

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def _validate_category(self, category: str) -> None:
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"invalid category {category!r}, must be one of "
                f"{sorted(VALID_CATEGORIES)}"
            )

    def add(
        self,
        email: str,
        reason: str,
        category: str,
        source: Optional[str] = None,
    ) -> None:
        """Insert or replace a suppression entry."""
        self._validate_category(category)
        norm = self._normalize_email(email)
        ts = int(time.time())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO suppressions (email, reason, category, added_ts, source)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    reason = excluded.reason,
                    category = excluded.category,
                    added_ts = excluded.added_ts,
                    source = excluded.source
                """,
                (norm, reason, category, ts, source),
            )

    def remove(self, email: str) -> bool:
        """Remove an address from the suppression list. Returns True if present."""
        norm = self._normalize_email(email)
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM suppressions WHERE email = ?", (norm,)
            )
            return cur.rowcount > 0

    def is_suppressed(self, email: str) -> tuple[bool, Optional[str]]:
        """
        Return (True, reason) if the address is suppressed.
        Soft bounces older than SOFT_BOUNCE_EXPIRY_DAYS are auto purged.
        """
        norm = self._normalize_email(email)
        cutoff = int(time.time()) - (SOFT_BOUNCE_EXPIRY_DAYS * SECONDS_PER_DAY)
        with self._connect() as conn:
            # Purge expired soft bounces for this address first.
            conn.execute(
                "DELETE FROM suppressions "
                "WHERE email = ? AND category = 'bounce_soft' AND added_ts < ?",
                (norm, cutoff),
            )
            row = conn.execute(
                "SELECT reason, category FROM suppressions WHERE email = ?",
                (norm,),
            ).fetchone()
            if row is None:
                return (False, None)
            return (True, f"{row['category']}: {row['reason']}")

    def bulk_add(self, items: list[dict]) -> int:
        """
        Add many suppressions in one transaction.
        Each item must have keys: email, reason, category.
        Optional key: source.
        """
        ts = int(time.time())
        rows = []
        for item in items:
            self._validate_category(item["category"])
            rows.append(
                (
                    self._normalize_email(item["email"]),
                    item["reason"],
                    item["category"],
                    ts,
                    item.get("source"),
                )
            )
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO suppressions (email, reason, category, added_ts, source)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    reason = excluded.reason,
                    category = excluded.category,
                    added_ts = excluded.added_ts,
                    source = excluded.source
                """,
                rows,
            )
        return len(rows)

    def import_from_csv(self, path: str) -> int:
        """
        Import suppressions from a CSV file.
        Required columns: email, reason, category.
        Optional column: source.
        """
        imported: list[dict] = []
        with open(path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            required = {"email", "reason", "category"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"CSV missing required columns: {sorted(missing)}")
            for row in reader:
                imported.append(
                    {
                        "email": row["email"],
                        "reason": row["reason"],
                        "category": row["category"],
                        "source": row.get("source"),
                    }
                )
        return self.bulk_add(imported)

    def export_to_csv(self, path: str) -> int:
        """Write the current suppression list to a CSV file."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT email, reason, category, added_ts, source "
                "FROM suppressions ORDER BY added_ts DESC"
            ).fetchall()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["email", "reason", "category", "added_ts", "source"])
            for row in rows:
                writer.writerow(
                    [
                        row["email"],
                        row["reason"],
                        row["category"],
                        row["added_ts"],
                        row["source"] or "",
                    ]
                )
        return len(rows)

    def stats(self) -> dict:
        """Return counts per category plus a total."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT category, COUNT(*) AS n FROM suppressions GROUP BY category"
            ).fetchall()
            total_row = conn.execute(
                "SELECT COUNT(*) AS n FROM suppressions"
            ).fetchone()
        out = {c: 0 for c in VALID_CATEGORIES}
        for r in rows:
            out[r["category"]] = r["n"]
        out["total"] = total_row["n"]
        return out

    def purge_expired_soft_bounces(self) -> int:
        """Remove all soft bounces older than SOFT_BOUNCE_EXPIRY_DAYS."""
        cutoff = int(time.time()) - (SOFT_BOUNCE_EXPIRY_DAYS * SECONDS_PER_DAY)
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM suppressions "
                "WHERE category = 'bounce_soft' AND added_ts < ?",
                (cutoff,),
            )
            return cur.rowcount
