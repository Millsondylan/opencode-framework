"""Social post scheduler for X, LinkedIn, Reddit.

Maintains a SQLite-backed queue of posts, enforces per-platform daily
rate limits, and distributes posts over time at a configurable cadence.

Integration stubs (post_to_x, post_to_linkedin, post_to_reddit) raise
NotImplementedError. Per open-items log, actual API integrations are
deferred to Run 8+.

Usage:
    python -m marketing.social.scheduler enqueue --platform x --content "..."
    python -m marketing.social.scheduler run-due
    python -m marketing.social.scheduler stats
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG = logging.getLogger("social_scheduler")

PLATFORMS = ("x", "linkedin", "reddit")

PLATFORM_RATE_LIMITS = {
    "x": 50,
    "linkedin": 20,
    "reddit": 10,
}

STATUS_PENDING = "pending"
STATUS_POSTED = "posted"
STATUS_FAILED = "failed"
STATUS_SUPPRESSED = "suppressed"


@dataclass
class Post:
    """A queued social media post."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    platform: str = "x"
    content: str = ""
    media_paths: list[str] = field(default_factory=list)
    scheduled_ts: int = 0
    status: str = STATUS_PENDING
    posted_ts: Optional[int] = None
    post_url: Optional[str] = None
    attempts: int = 0
    last_error: Optional[str] = None

    def validate(self) -> None:
        if self.platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {PLATFORMS}, got {self.platform}")
        if not self.content or not self.content.strip():
            raise ValueError("content required")
        if self.platform == "x" and len(self.content) > 280:
            raise ValueError("X posts limited to 280 chars")
        if self.platform == "linkedin" and len(self.content) > 3000:
            raise ValueError("LinkedIn posts limited to 3000 chars")
        if self.platform == "reddit" and len(self.content) > 40000:
            raise ValueError("Reddit posts limited to 40000 chars")


class SocialScheduler:
    """SQLite-backed queue with per-platform rate limiting."""

    def __init__(
        self,
        queue_db_path: str = "~/.opencode/social_queue.sqlite",
        platform_rate_limits: Optional[dict[str, int]] = None,
    ) -> None:
        self.queue_db_path = Path(os.path.expanduser(queue_db_path))
        self.queue_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.platform_rate_limits = platform_rate_limits or dict(PLATFORM_RATE_LIMITS)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.queue_db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS posts (
                  id TEXT PRIMARY KEY,
                  platform TEXT NOT NULL,
                  content TEXT NOT NULL,
                  media TEXT,
                  scheduled_ts INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  posted_ts INTEGER,
                  post_url TEXT,
                  attempts INTEGER NOT NULL DEFAULT 0,
                  last_error TEXT,
                  created_ts INTEGER NOT NULL DEFAULT (CAST(strftime('%s','now') AS INTEGER))
                );
                CREATE INDEX IF NOT EXISTS idx_posts_due
                  ON posts (status, scheduled_ts);
                CREATE INDEX IF NOT EXISTS idx_posts_platform_day
                  ON posts (platform, posted_ts);
                """
            )

    def enqueue(self, post: Post) -> str:
        """Insert a post into the queue."""
        post.validate()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO posts (id, platform, content, media, scheduled_ts, status,
                                   posted_ts, post_url, attempts, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.id,
                    post.platform,
                    post.content,
                    json.dumps(post.media_paths),
                    int(post.scheduled_ts),
                    post.status,
                    post.posted_ts,
                    post.post_url,
                    post.attempts,
                    post.last_error,
                ),
            )
        return post.id

    def _row_to_post(self, row: sqlite3.Row) -> Post:
        return Post(
            id=row["id"],
            platform=row["platform"],
            content=row["content"],
            media_paths=json.loads(row["media"] or "[]"),
            scheduled_ts=int(row["scheduled_ts"]),
            status=row["status"],
            posted_ts=row["posted_ts"],
            post_url=row["post_url"],
            attempts=int(row["attempts"] or 0),
            last_error=row["last_error"],
        )

    def dequeue_due(self, now_ts: Optional[int] = None) -> list[Post]:
        """Return pending posts with scheduled_ts <= now."""
        now_ts = now_ts if now_ts is not None else int(time.time())
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM posts
                WHERE status = ? AND scheduled_ts <= ?
                ORDER BY scheduled_ts ASC
                """,
                (STATUS_PENDING, now_ts),
            ).fetchall()
        return [self._row_to_post(r) for r in rows]

    def _posts_today(self, platform: str, now_ts: int) -> int:
        """Count posts already made on this platform in the current UTC day."""
        day_start = int(
            datetime.fromtimestamp(now_ts, tz=timezone.utc)
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS n FROM posts
                WHERE platform = ? AND status = ? AND posted_ts >= ?
                """,
                (platform, STATUS_POSTED, day_start),
            ).fetchone()
        return int(row["n"] if row else 0)

    def can_post_now(self, platform: str, now_ts: Optional[int] = None) -> bool:
        """True if platform daily rate limit not yet hit."""
        now_ts = now_ts if now_ts is not None else int(time.time())
        limit = self.platform_rate_limits.get(platform, 0)
        return self._posts_today(platform, now_ts) < limit

    def mark_posted(self, post_id: str, post_url: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE posts SET status = ?, post_url = ?, posted_ts = ?
                WHERE id = ?
                """,
                (STATUS_POSTED, post_url, int(time.time()), post_id),
            )

    def mark_failed(self, post_id: str, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE posts
                SET status = ?, last_error = ?, attempts = attempts + 1
                WHERE id = ?
                """,
                (STATUS_FAILED, error[:500], post_id),
            )

    def mark_suppressed(self, post_id: str, reason: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE posts SET status = ?, last_error = ? WHERE id = ?",
                (STATUS_SUPPRESSED, reason[:500], post_id),
            )

    def generate_schedule(
        self,
        posts: list[Post],
        start_ts: int,
        cadence_hours: int = 4,
    ) -> list[Post]:
        """Distribute posts over time, respecting per-platform daily caps.

        Cadence is the minimum spacing between posts of the same platform.
        If cap is reached for a day, subsequent posts roll into the next day.
        """
        cadence_seconds = max(1, int(cadence_hours)) * 3600
        next_slot: dict[str, int] = {p: start_ts for p in PLATFORMS}
        day_counts: dict[tuple[str, int], int] = {}

        scheduled: list[Post] = []
        for post in posts:
            post.validate()
            platform = post.platform
            candidate = next_slot[platform]
            while True:
                day_bucket = int(
                    datetime.fromtimestamp(candidate, tz=timezone.utc)
                    .replace(hour=0, minute=0, second=0, microsecond=0)
                    .timestamp()
                )
                key = (platform, day_bucket)
                count = day_counts.get(key, 0)
                limit = self.platform_rate_limits.get(platform, 0)
                if count < limit:
                    day_counts[key] = count + 1
                    post.scheduled_ts = candidate
                    next_slot[platform] = candidate + cadence_seconds
                    scheduled.append(post)
                    break
                candidate = day_bucket + 86400
        return scheduled

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM posts").fetchone()["n"]
            by_status: dict[str, int] = {}
            for row in conn.execute(
                "SELECT status, COUNT(*) AS n FROM posts GROUP BY status"
            ).fetchall():
                by_status[row["status"]] = int(row["n"])
            by_platform: dict[str, int] = {}
            for row in conn.execute(
                "SELECT platform, COUNT(*) AS n FROM posts GROUP BY platform"
            ).fetchall():
                by_platform[row["platform"]] = int(row["n"])
        return {"total": int(total), **{f"status_{k}": v for k, v in by_status.items()}, **{f"platform_{k}": v for k, v in by_platform.items()}}


def post_to_x(post: Post) -> str:
    """Send to X / Twitter. Returns post URL.

    Deferred to Run 8+. See docs/open-items.md entry social_x_integration.
    """
    raise NotImplementedError("X integration deferred to Run 8+")


def post_to_linkedin(post: Post) -> str:
    """Send to LinkedIn. Returns post URL.

    Deferred to Run 8+. See docs/open-items.md entry social_linkedin_integration.
    """
    raise NotImplementedError("LinkedIn integration deferred to Run 8+")


def post_to_reddit(post: Post) -> str:
    """Send to Reddit. Returns post URL.

    Deferred to Run 8+. See docs/open-items.md entry social_reddit_integration.
    """
    raise NotImplementedError("Reddit integration deferred to Run 8+")


PLATFORM_DISPATCH = {
    "x": post_to_x,
    "linkedin": post_to_linkedin,
    "reddit": post_to_reddit,
}


def run_due(scheduler: SocialScheduler) -> dict[str, int]:
    """Iterate due posts, attempt dispatch, update status. Returns counts."""
    due = scheduler.dequeue_due()
    counts = {"attempted": 0, "posted": 0, "failed": 0, "suppressed": 0}
    for post in due:
        counts["attempted"] += 1
        if not scheduler.can_post_now(post.platform):
            scheduler.mark_suppressed(post.id, "daily_rate_limit_exceeded")
            counts["suppressed"] += 1
            continue
        fn = PLATFORM_DISPATCH.get(post.platform)
        if fn is None:
            scheduler.mark_failed(post.id, "unknown_platform")
            counts["failed"] += 1
            continue
        try:
            url = fn(post)
            scheduler.mark_posted(post.id, url)
            counts["posted"] += 1
        except NotImplementedError as exc:
            scheduler.mark_failed(post.id, f"integration_pending:{exc}")
            counts["failed"] += 1
        except Exception as exc:
            scheduler.mark_failed(post.id, str(exc))
            counts["failed"] += 1
    return counts


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Social post scheduler")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enq = sub.add_parser("enqueue")
    p_enq.add_argument("--platform", required=True, choices=PLATFORMS)
    p_enq.add_argument("--content", required=True)
    p_enq.add_argument("--scheduled-ts", type=int, default=0)
    p_enq.add_argument("--media", action="append", default=[])

    sub.add_parser("run-due")
    sub.add_parser("stats")

    p_sched = sub.add_parser("schedule-file")
    p_sched.add_argument("--file", required=True, help="JSON file with list of posts")
    p_sched.add_argument("--start-ts", type=int, default=int(time.time()))
    p_sched.add_argument("--cadence-hours", type=int, default=4)

    args = parser.parse_args()
    sched = SocialScheduler()

    if args.cmd == "enqueue":
        p = Post(
            platform=args.platform,
            content=args.content,
            media_paths=args.media,
            scheduled_ts=args.scheduled_ts or int(time.time()),
        )
        pid = sched.enqueue(p)
        print(pid)
        return 0

    if args.cmd == "run-due":
        counts = run_due(sched)
        print(json.dumps(counts))
        return 0

    if args.cmd == "stats":
        print(json.dumps(sched.stats(), indent=2))
        return 0

    if args.cmd == "schedule-file":
        raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
        posts = [
            Post(
                platform=item["platform"],
                content=item["content"],
                media_paths=item.get("media_paths", []),
            )
            for item in raw
        ]
        scheduled = sched.generate_schedule(posts, args.start_ts, args.cadence_hours)
        for p in scheduled:
            sched.enqueue(p)
        print(json.dumps({"enqueued": len(scheduled)}))
        return 0

    return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(_cli())
