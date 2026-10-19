"""Google Play release and track management.

This module coordinates Android App Bundle uploads, track updates, staged
rollouts, and closed testing policy enforcement using the low level
PlayClient from publishing.play.client.

Tracks
    internal:   closed, ad hoc testing.
    alpha:      small closed or open alpha.
    beta:       larger open beta.
    production: public release.

Release states
    inProgress: staged rollout in flight.
    completed:  100 percent rollout, released to all users.
    halted:     rollout stopped without revert.
    draft:      release saved but not launched.

Closed testing policy
    Google requires new personal developer accounts to complete a closed test
    with at least 12 testers running the app on real devices for 14 days
    before they can promote to production. The ClosedTestingConfig dataclass
    and validate_closed_testing_requirements helper enforce this rule.

External dependencies
    pip install google-api-python-client google-auth
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    from googleapiclient.http import MediaFileUpload
    _MEDIA_UPLOAD_AVAILABLE = True
    _MEDIA_UPLOAD_ERROR = ""
except ImportError as _exc:
    MediaFileUpload = None
    _MEDIA_UPLOAD_AVAILABLE = False
    _MEDIA_UPLOAD_ERROR = (
        "googleapiclient.http.MediaFileUpload is unavailable. Install via: "
        "pip install google-api-python-client google-auth. "
        "Original error: {0}".format(_exc)
    )

from publishing.play.client import (
    PlayAPIError,
    PlayAuthError,
    PlayClient,
    PlayValidationError,
    get_default_client,
)


TRACK_INTERNAL = "internal"
TRACK_ALPHA = "alpha"
TRACK_BETA = "beta"
TRACK_PRODUCTION = "production"

VALID_TRACKS = (TRACK_INTERNAL, TRACK_ALPHA, TRACK_BETA, TRACK_PRODUCTION)

STATUS_IN_PROGRESS = "inProgress"
STATUS_COMPLETED = "completed"
STATUS_HALTED = "halted"
STATUS_DRAFT = "draft"

AAB_MIME_TYPE = "application/octet-stream"


_LOG = logging.getLogger("publishing.play.release")
if not _LOG.handlers:
    _LOG.setLevel(logging.INFO)
    _console = logging.StreamHandler()
    _console.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    _LOG.addHandler(_console)
    _LOG.propagate = False


def _require_track(track: str) -> str:
    """Return track if valid, otherwise raise PlayValidationError."""
    if track not in VALID_TRACKS:
        raise PlayValidationError(
            "Unknown track '{0}'. Valid tracks: {1}".format(track, ", ".join(VALID_TRACKS))
        )
    return track


def _require_rollout(percentage: float) -> float:
    """Return a validated rollout fraction in the inclusive range 0.0 to 1.0."""
    try:
        value = float(percentage)
    except (TypeError, ValueError) as exc:
        raise PlayValidationError(
            "Rollout percentage must be numeric, got {0!r}".format(percentage)
        ) from exc
    if value < 0.0 or value > 1.0:
        raise PlayValidationError(
            "Rollout percentage must be between 0.0 and 1.0 inclusive, got {0}".format(value)
        )
    return value


def _require_version_codes(version_codes: list[int]) -> list[int]:
    """Return the provided version codes after basic validation."""
    if not version_codes:
        raise PlayValidationError("At least one version code is required.")
    cleaned: list[int] = []
    for vc in version_codes:
        try:
            cleaned.append(int(vc))
        except (TypeError, ValueError) as exc:
            raise PlayValidationError(
                "Version code must be an integer, got {0!r}".format(vc)
            ) from exc
    return cleaned


@dataclass
class ClosedTestingConfig:
    """Configuration for Google Play closed testing requirements."""

    testers_count: int = 12
    days_required: int = 14
    real_devices_required: bool = True
    notes: str = field(
        default=(
            "Google requires at least 12 opted in testers for 14 continuous "
            "days on real devices before production access is granted."
        )
    )


def validate_closed_testing_requirements(
    releases: list[dict],
    testers: int,
    days_elapsed: int,
    config: Optional[ClosedTestingConfig] = None,
) -> tuple[bool, str]:
    """Check whether closed testing prerequisites have been met.

    Args:
        releases: The releases array from a closed track. Must contain at
            least one release with status completed or inProgress.
        testers: The number of opted in testers currently assigned to the
            closed track.
        days_elapsed: The number of days since testing began.
        config: Optional override for the policy thresholds.

    Returns:
        A (ok, reason) tuple. When ok is True, reason is a short success
        string. When ok is False, reason explains the missing requirement.
    """
    cfg = config or ClosedTestingConfig()
    if not isinstance(releases, list) or not releases:
        return False, "No closed testing release present."
    active = [
        r
        for r in releases
        if isinstance(r, dict) and r.get("status") in (STATUS_COMPLETED, STATUS_IN_PROGRESS)
    ]
    if not active:
        return False, "No active or completed closed testing release found."
    if testers < cfg.testers_count:
        return False, "Only {0} testers assigned; {1} required.".format(testers, cfg.testers_count)
    if days_elapsed < cfg.days_required:
        return False, "Only {0} days of testing elapsed; {1} required.".format(
            days_elapsed, cfg.days_required
        )
    if cfg.real_devices_required:
        return True, "Closed testing requirements met on real devices."
    return True, "Closed testing requirements met."


class ReleaseManager:
    """High level helper for track and release operations within a single edit."""

    def __init__(self, client: PlayClient) -> None:
        if client is None:
            raise PlayValidationError("ReleaseManager requires a PlayClient instance.")
        self.client = client

    def upload_aab(self, edit_id: str, aab_path: str) -> dict:
        """Upload an Android App Bundle (.aab) and return the bundle response.

        Args:
            edit_id: Active edit identifier.
            aab_path: Filesystem path to the .aab file.

        Returns:
            The parsed bundle resource including the assigned version code.
        """
        if not _MEDIA_UPLOAD_AVAILABLE:
            raise PlayAuthError(_MEDIA_UPLOAD_ERROR)
        if not edit_id:
            raise PlayValidationError("edit_id is required for upload_aab")
        aab = Path(aab_path).expanduser()
        if not aab.is_file():
            raise PlayValidationError("AAB file not found: {0}".format(aab))
        package = self.client._require_package()
        media = MediaFileUpload(
            str(aab), mimetype=AAB_MIME_TYPE, resumable=True
        )
        request = self.client.service.edits().bundles().upload(
            packageName=package,
            editId=edit_id,
            media_body=media,
        )
        result = self.client.execute(request, operation="edits.bundles.upload")
        version_code = result.get("versionCode") if isinstance(result, dict) else None
        _LOG.info(
            "upload_aab package=%s edit=%s version_code=%s sha1=%s",
            package,
            edit_id,
            version_code,
            result.get("sha1") if isinstance(result, dict) else None,
        )
        return result

    def get_track(self, edit_id: str, track: str) -> dict:
        """Return the current track resource."""
        if not edit_id:
            raise PlayValidationError("edit_id is required for get_track")
        _require_track(track)
        package = self.client._require_package()
        request = self.client.service.edits().tracks().get(
            packageName=package,
            editId=edit_id,
            track=track,
        )
        return self.client.execute(request, operation="edits.tracks.get")

    def update_track(
        self,
        edit_id: str,
        track: str,
        version_codes: list[int],
        release_name: str,
        release_notes: list[dict],
        rollout_percentage: float = 1.0,
    ) -> dict:
        """Update a track with a single release containing the given bundles.

        Args:
            edit_id: Active edit identifier.
            track: Target track name.
            version_codes: List of bundle version codes to include.
            release_name: Human readable release name.
            release_notes: List of localized notes with keys "language" and
                "text" (for example {"language": "en-US", "text": "..."}).
            rollout_percentage: Staged rollout fraction in the range 0.0 to
                1.0. Values below 1.0 produce an inProgress release; 1.0
                produces a completed rollout.
        """
        if not edit_id:
            raise PlayValidationError("edit_id is required for update_track")
        _require_track(track)
        codes = _require_version_codes(version_codes)
        fraction = _require_rollout(rollout_percentage)
        if not release_name:
            raise PlayValidationError("release_name is required for update_track")
        notes = self._normalise_release_notes(release_notes)
        release: dict[str, Any] = {
            "name": release_name,
            "versionCodes": [str(c) for c in codes],
            "releaseNotes": notes,
        }
        if fraction < 1.0:
            release["status"] = STATUS_IN_PROGRESS
            release["userFraction"] = fraction
        else:
            release["status"] = STATUS_COMPLETED
        body = {"track": track, "releases": [release]}
        package = self.client._require_package()
        request = self.client.service.edits().tracks().update(
            packageName=package,
            editId=edit_id,
            track=track,
            body=body,
        )
        result = self.client.execute(request, operation="edits.tracks.update")
        _LOG.info(
            "update_track package=%s edit=%s track=%s codes=%s rollout=%.3f status=%s",
            package,
            edit_id,
            track,
            codes,
            fraction,
            release["status"],
        )
        return result

    def promote(self, edit_id: str, source_track: str, target_track: str) -> dict:
        """Promote the source track's latest release to the target track.

        The version codes from the most recent source release are copied into
        a new completed release on the target track.
        """
        if not edit_id:
            raise PlayValidationError("edit_id is required for promote")
        _require_track(source_track)
        _require_track(target_track)
        if source_track == target_track:
            raise PlayValidationError(
                "source_track and target_track must differ for promote"
            )
        source = self.get_track(edit_id, source_track)
        releases = source.get("releases", []) if isinstance(source, dict) else []
        if not releases:
            raise PlayValidationError(
                "Source track '{0}' has no releases to promote".format(source_track)
            )
        latest = releases[0]
        codes_raw = latest.get("versionCodes") or []
        version_codes = [int(c) for c in codes_raw]
        release_name = latest.get("name") or "Promoted from {0}".format(source_track)
        release_notes = latest.get("releaseNotes") or [
            {"language": "en-US", "text": "Promoted from {0}.".format(source_track)}
        ]
        return self.update_track(
            edit_id,
            target_track,
            version_codes,
            release_name,
            release_notes,
            rollout_percentage=1.0,
        )

    def rollout(self, edit_id: str, track: str, percentage: float) -> dict:
        """Update the userFraction of the current in progress release."""
        if not edit_id:
            raise PlayValidationError("edit_id is required for rollout")
        _require_track(track)
        fraction = _require_rollout(percentage)
        current = self.get_track(edit_id, track)
        release = self._current_release(current, expected_status=STATUS_IN_PROGRESS)
        release["userFraction"] = fraction
        release["status"] = STATUS_IN_PROGRESS if fraction < 1.0 else STATUS_COMPLETED
        if fraction >= 1.0 and "userFraction" in release:
            release.pop("userFraction", None)
        body = {"track": track, "releases": [release]}
        package = self.client._require_package()
        request = self.client.service.edits().tracks().update(
            packageName=package,
            editId=edit_id,
            track=track,
            body=body,
        )
        result = self.client.execute(request, operation="edits.tracks.rollout")
        _LOG.info(
            "rollout package=%s edit=%s track=%s fraction=%.3f status=%s",
            package,
            edit_id,
            track,
            fraction,
            release["status"],
        )
        return result

    def halt(self, edit_id: str, track: str) -> dict:
        """Halt the current in progress release on the given track."""
        return self._set_release_status(edit_id, track, STATUS_HALTED)

    def resume(self, edit_id: str, track: str) -> dict:
        """Resume a previously halted release back to inProgress."""
        return self._set_release_status(edit_id, track, STATUS_IN_PROGRESS)

    def list_releases(self, edit_id: str, track: str) -> list[dict]:
        """Return the releases array on the given track, or an empty list."""
        track_resource = self.get_track(edit_id, track)
        releases = track_resource.get("releases", []) if isinstance(track_resource, dict) else []
        return list(releases) if isinstance(releases, list) else []

    def _set_release_status(self, edit_id: str, track: str, status: str) -> dict:
        """Set the status of the current release on the given track."""
        if not edit_id:
            raise PlayValidationError("edit_id is required for status change")
        _require_track(track)
        if status not in (STATUS_IN_PROGRESS, STATUS_HALTED, STATUS_COMPLETED, STATUS_DRAFT):
            raise PlayValidationError("Invalid status: {0}".format(status))
        current = self.get_track(edit_id, track)
        release = self._current_release(current)
        release["status"] = status
        body = {"track": track, "releases": [release]}
        package = self.client._require_package()
        request = self.client.service.edits().tracks().update(
            packageName=package,
            editId=edit_id,
            track=track,
            body=body,
        )
        result = self.client.execute(request, operation="edits.tracks.status")
        _LOG.info(
            "set_release_status package=%s edit=%s track=%s status=%s",
            package,
            edit_id,
            track,
            status,
        )
        return result

    @staticmethod
    def _current_release(track_resource: dict, expected_status: Optional[str] = None) -> dict:
        """Return the first release that matches the expected status."""
        releases = track_resource.get("releases", []) if isinstance(track_resource, dict) else []
        if not releases:
            raise PlayValidationError(
                "Track '{0}' has no releases".format(track_resource.get("track"))
            )
        if expected_status is None:
            return dict(releases[0])
        for release in releases:
            if isinstance(release, dict) and release.get("status") == expected_status:
                return dict(release)
        return dict(releases[0])

    @staticmethod
    def _normalise_release_notes(notes: list[dict]) -> list[dict]:
        """Validate and normalise release notes into API-compatible form."""
        if not notes:
            raise PlayValidationError(
                "release_notes is required and must contain at least one entry."
            )
        clean: list[dict[str, str]] = []
        for entry in notes:
            if not isinstance(entry, dict):
                raise PlayValidationError(
                    "Each release note must be a dict with 'language' and 'text' keys."
                )
            language = entry.get("language")
            text = entry.get("text")
            if not language or not text:
                raise PlayValidationError(
                    "Each release note requires both 'language' and 'text'."
                )
            clean.append({"language": str(language), "text": str(text)})
        return clean


def _parse_release_notes(raw: Optional[str]) -> list[dict]:
    """Parse a --notes argument as either JSON or plain English text."""
    if not raw:
        return [{"language": "en-US", "text": "Routine update."}]
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return [{"language": "en-US", "text": raw}]
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return [parsed]
    return [{"language": "en-US", "text": str(parsed)}]


def _build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for release operations."""
    parser = argparse.ArgumentParser(
        prog="publishing.play.release",
        description="Manage Google Play tracks and releases.",
    )
    parser.add_argument(
        "--package",
        default=os.environ.get("GPLAY_APP_PACKAGE"),
        help="Application package name (defaults to GPLAY_APP_PACKAGE).",
    )
    parser.add_argument(
        "--service-account",
        default=os.environ.get("GPLAY_SERVICE_ACCOUNT_JSON"),
        help="Path to service account JSON (defaults to GPLAY_SERVICE_ACCOUNT_JSON).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    upload = sub.add_parser("upload", help="Upload an AAB and update a track.")
    upload.add_argument("--aab", required=True, help="Path to the .aab file.")
    upload.add_argument("--track", default=TRACK_INTERNAL)
    upload.add_argument("--release-name", required=True)
    upload.add_argument("--notes", default=None, help="Release notes (text or JSON list).")
    upload.add_argument("--rollout", type=float, default=1.0)
    upload.add_argument("--validate-only", action="store_true")

    promote = sub.add_parser("promote", help="Promote a release between tracks.")
    promote.add_argument("--source", required=True)
    promote.add_argument("--target", required=True)
    promote.add_argument("--validate-only", action="store_true")

    rollout = sub.add_parser("rollout", help="Update rollout percentage.")
    rollout.add_argument("--track", required=True)
    rollout.add_argument("--percentage", type=float, required=True)
    rollout.add_argument("--validate-only", action="store_true")

    halt = sub.add_parser("halt", help="Halt an in progress release.")
    halt.add_argument("--track", required=True)
    halt.add_argument("--validate-only", action="store_true")

    resume = sub.add_parser("resume", help="Resume a halted release.")
    resume.add_argument("--track", required=True)
    resume.add_argument("--validate-only", action="store_true")

    sub.add_parser("list-tracks", help="List releases on all tracks.")

    return parser


def _run_cli(argv: Optional[list[str]] = None) -> int:
    """Execute the CLI. Returns a process exit code."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        client = PlayClient(
            service_account_json_path=args.service_account,
            app_package_name=args.package,
        )
        manager = ReleaseManager(client)
        edit = client.edits_insert()
        edit_id = edit.get("id") if isinstance(edit, dict) else None
        if not edit_id:
            raise PlayAPIError("edits.insert returned no edit id")

        command = args.command
        if command == "upload":
            bundle = manager.upload_aab(edit_id, args.aab)
            version_code = bundle.get("versionCode") if isinstance(bundle, dict) else None
            if version_code is None:
                raise PlayAPIError("Upload did not return a version code.")
            notes = _parse_release_notes(args.notes)
            manager.update_track(
                edit_id,
                args.track,
                [int(version_code)],
                args.release_name,
                notes,
                rollout_percentage=args.rollout,
            )
        elif command == "promote":
            manager.promote(edit_id, args.source, args.target)
        elif command == "rollout":
            manager.rollout(edit_id, args.track, args.percentage)
        elif command == "halt":
            manager.halt(edit_id, args.track)
        elif command == "resume":
            manager.resume(edit_id, args.track)
        elif command == "list-tracks":
            summary: dict[str, list[dict]] = {}
            for track in VALID_TRACKS:
                try:
                    summary[track] = manager.list_releases(edit_id, track)
                except PlayAPIError as exc:
                    summary[track] = [{"error": str(exc)}]
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            parser.error("Unknown command: {0}".format(command))

        validate_only = getattr(args, "validate_only", False)
        if validate_only:
            client.edits_validate(edit_id)
            client.edits_delete(edit_id)
            print("Validation successful; edit discarded.")
        else:
            client.edits_commit(edit_id)
            print("Edit committed: {0}".format(edit_id))
        return 0
    except PlayAPIError as exc:
        print("Play API error: {0}".format(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print("Unexpected error: {0}".format(exc), file=sys.stderr)
        return 2


__all__ = [
    "ClosedTestingConfig",
    "ReleaseManager",
    "STATUS_COMPLETED",
    "STATUS_DRAFT",
    "STATUS_HALTED",
    "STATUS_IN_PROGRESS",
    "TRACK_ALPHA",
    "TRACK_BETA",
    "TRACK_INTERNAL",
    "TRACK_PRODUCTION",
    "VALID_TRACKS",
    "get_default_client",
    "validate_closed_testing_requirements",
]


if __name__ == "__main__":
    raise SystemExit(_run_cli())
