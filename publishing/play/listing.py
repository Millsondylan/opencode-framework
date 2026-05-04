"""Google Play store listing management.

This module provides helpers for managing per locale store listings on
Google Play using the Android Publisher API v3. It wraps the
edits.listings and edits.images resources to support title, short
description, full description, promotional video URL, and image asset
uploads for all required image slots.

Target locales
    The TARGET_LOCALES constant enumerates the 10 locales the product
    ships with. Each locale gets an independent listing resource.

Image types
    featureGraphic:      1024x500 JPEG or 24 bit PNG. Required.
    icon:                512x512 PNG. Required for the store listing.
    promoGraphic:        180x120 JPEG or 24 bit PNG. Legacy.
    phoneScreenshots:    2 to 8 phone screenshots, 16:9 or 9:16 friendly.
    sevenInchScreenshots, tenInchScreenshots: tablet screenshots.
    tvScreenshots, tvBanner, wearScreenshots: form factor specific.

Field length limits
    title:             up to 30 characters.
    shortDescription:  up to 80 characters.
    fullDescription:   up to 4000 characters.

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


_LOG = logging.getLogger("publishing.play.listing")
if not _LOG.handlers:
    _LOG.addHandler(logging.NullHandler())


TARGET_LOCALES: list[str] = [
    "en-US",
    "es-ES",
    "pt-BR",
    "de-DE",
    "fr-FR",
    "ja-JP",
    "ko-KR",
    "hi-IN",
    "id-ID",
    "ar",
]

IMAGE_TYPES: list[str] = [
    "featureGraphic",
    "icon",
    "phoneScreenshots",
    "sevenInchScreenshots",
    "tenInchScreenshots",
    "promoGraphic",
    "tvScreenshots",
    "wearScreenshots",
    "tvBanner",
]

MULTI_IMAGE_TYPES: set[str] = {
    "phoneScreenshots",
    "sevenInchScreenshots",
    "tenInchScreenshots",
    "tvScreenshots",
    "wearScreenshots",
}

TITLE_MAX_CHARS = 30
SHORT_DESCRIPTION_MAX_CHARS = 80
FULL_DESCRIPTION_MAX_CHARS = 4000

MAX_IMAGE_BYTES = 1 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class FeatureGraphicConfig:
    """Configuration constraints for a Play store feature graphic asset."""

    width: int = 1024
    height: int = 500
    max_bytes: int = MAX_IMAGE_BYTES
    allowed_formats: tuple[str, ...] = ("png", "jpg", "jpeg")

    def describe(self) -> str:
        """Return a short human readable description of the constraints."""
        return "{0}x{1} {2}, up to {3} bytes".format(
            self.width,
            self.height,
            "/".join(self.allowed_formats),
            self.max_bytes,
        )


@dataclass(frozen=True)
class IconConfig:
    """Configuration constraints for a Play store high resolution icon."""

    width: int = 512
    height: int = 512
    max_bytes: int = MAX_IMAGE_BYTES
    allowed_formats: tuple[str, ...] = ("png",)

    def describe(self) -> str:
        """Return a short human readable description of the constraints."""
        return "{0}x{1} {2}, up to {3} bytes".format(
            self.width,
            self.height,
            "/".join(self.allowed_formats),
            self.max_bytes,
        )


def validate_listing_fields(
    title: str,
    short_description: str,
    full_description: str,
) -> tuple[bool, str]:
    """Validate listing fields against Play store length limits.

    Returns a tuple of (is_valid, message). When invalid, message
    explains which field failed. When valid, message is "ok".
    """
    if title is None or not isinstance(title, str):
        return False, "title must be a non empty string"
    if short_description is None or not isinstance(short_description, str):
        return False, "short_description must be a non empty string"
    if full_description is None or not isinstance(full_description, str):
        return False, "full_description must be a non empty string"
    title_trim = title.strip()
    short_trim = short_description.strip()
    full_trim = full_description.strip()
    if not title_trim:
        return False, "title is empty after trimming whitespace"
    if not short_trim:
        return False, "short_description is empty after trimming whitespace"
    if not full_trim:
        return False, "full_description is empty after trimming whitespace"
    if len(title) > TITLE_MAX_CHARS:
        return False, "title exceeds {0} characters (got {1})".format(
            TITLE_MAX_CHARS, len(title)
        )
    if len(short_description) > SHORT_DESCRIPTION_MAX_CHARS:
        return False, "short_description exceeds {0} characters (got {1})".format(
            SHORT_DESCRIPTION_MAX_CHARS, len(short_description)
        )
    if len(full_description) > FULL_DESCRIPTION_MAX_CHARS:
        return False, "full_description exceeds {0} characters (got {1})".format(
            FULL_DESCRIPTION_MAX_CHARS, len(full_description)
        )
    return True, "ok"


def _validate_image_file(image_path: str) -> Path:
    """Validate an image file path and return a resolved Path."""
    if not image_path:
        raise PlayValidationError("image_path is required")
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise PlayValidationError(
            "image file not found: {0}".format(path)
        )
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise PlayValidationError(
            "image extension {0} not in {1}".format(suffix, sorted(ALLOWED_IMAGE_EXTENSIONS))
        )
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise PlayValidationError(
            "failed to read image size: {0}".format(exc)
        ) from exc
    if size <= 0:
        raise PlayValidationError("image file is empty: {0}".format(path))
    if size > MAX_IMAGE_BYTES:
        raise PlayValidationError(
            "image file {0} exceeds {1} bytes (got {2})".format(
                path, MAX_IMAGE_BYTES, size
            )
        )
    return path


def _mime_for(path: Path) -> str:
    """Return the mime type for a supported image extension."""
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    return "image/jpeg"


class ListingManager:
    """Manage per locale store listings and image assets for a package."""

    def __init__(self, client: Optional[PlayClient] = None) -> None:
        """Initialise the manager.

        Args:
            client: An authenticated PlayClient. When None, uses the
                module default client loaded from environment variables.
        """
        self.client = client if client is not None else get_default_client()

    def _package(self) -> str:
        """Return the configured package name, raising if missing."""
        package = self.client.app_package_name
        if not package:
            raise PlayAuthError(
                "Application package name is not configured on PlayClient."
            )
        return package

    def get_listing(self, edit_id: str, language: str) -> dict:
        """Return the listing resource for a specific locale."""
        if not edit_id:
            raise PlayValidationError("edit_id is required")
        if not language:
            raise PlayValidationError("language is required")
        package = self._package()
        request = self.client.service.edits().listings().get(
            packageName=package,
            editId=edit_id,
            language=language,
        )
        return self.client.execute(request, operation="edits.listings.get")

    def update_listing(
        self,
        edit_id: str,
        language: str,
        title: str,
        short_desc: str,
        full_desc: str,
        video: Optional[str] = None,
    ) -> dict:
        """Update title, descriptions, and optional video URL for a locale.

        Enforces Play store length limits before calling the API.
        """
        if not edit_id:
            raise PlayValidationError("edit_id is required")
        if not language:
            raise PlayValidationError("language is required")
        ok, message = validate_listing_fields(title, short_desc, full_desc)
        if not ok:
            raise PlayValidationError(
                "listing validation failed for {0}: {1}".format(language, message)
            )
        package = self._package()
        body: dict[str, Any] = {
            "language": language,
            "title": title,
            "shortDescription": short_desc,
            "fullDescription": full_desc,
        }
        if video:
            body["video"] = video
        request = self.client.service.edits().listings().update(
            packageName=package,
            editId=edit_id,
            language=language,
            body=body,
        )
        result = self.client.execute(
            request, operation="edits.listings.update"
        )
        _LOG.info(
            "listing.update language=%s title_len=%d short_len=%d full_len=%d",
            language,
            len(title),
            len(short_desc),
            len(full_desc),
        )
        return result

    def upload_image(
        self,
        edit_id: str,
        language: str,
        image_type: str,
        image_path: str,
    ) -> dict:
        """Upload a single image for a given locale and image type.

        Validates extension and size before uploading.
        """
        if not edit_id:
            raise PlayValidationError("edit_id is required")
        if not language:
            raise PlayValidationError("language is required")
        if image_type not in IMAGE_TYPES:
            raise PlayValidationError(
                "image_type {0} is not one of {1}".format(image_type, IMAGE_TYPES)
            )
        if not _MEDIA_UPLOAD_AVAILABLE:
            raise PlayAPIError(_MEDIA_UPLOAD_ERROR)
        resolved = _validate_image_file(image_path)
        package = self._package()
        media = MediaFileUpload(
            str(resolved),
            mimetype=_mime_for(resolved),
            resumable=True,
        )
        request = self.client.service.edits().images().upload(
            packageName=package,
            editId=edit_id,
            language=language,
            imageType=image_type,
            media_body=media,
        )
        result = self.client.execute(
            request,
            operation="edits.images.upload:{0}".format(image_type),
        )
        _LOG.info(
            "image.upload language=%s type=%s path=%s",
            language,
            image_type,
            resolved.name,
        )
        return result

    def delete_all_images(
        self,
        edit_id: str,
        language: str,
        image_type: str,
    ) -> dict:
        """Delete every image of a given type for a locale.

        Used to clear slot contents prior to a batch upload so that the
        new set of assets fully replaces any stale ones.
        """
        if not edit_id:
            raise PlayValidationError("edit_id is required")
        if not language:
            raise PlayValidationError("language is required")
        if image_type not in IMAGE_TYPES:
            raise PlayValidationError(
                "image_type {0} is not one of {1}".format(image_type, IMAGE_TYPES)
            )
        package = self._package()
        request = self.client.service.edits().images().deleteall(
            packageName=package,
            editId=edit_id,
            language=language,
            imageType=image_type,
        )
        result = self.client.execute(
            request,
            operation="edits.images.deleteall:{0}".format(image_type),
        )
        _LOG.info(
            "image.deleteall language=%s type=%s",
            language,
            image_type,
        )
        return result if result is not None else {}

    def upload_screenshots(
        self,
        edit_id: str,
        language: str,
        phone_paths: Optional[list[str]] = None,
        tablet7_paths: Optional[list[str]] = None,
        tablet10_paths: Optional[list[str]] = None,
    ) -> dict[str, list[dict]]:
        """Upload phone and tablet screenshots for a locale.

        Clears each multi image slot first so the uploaded set fully
        replaces the existing assets. Returns a mapping of image type to
        the list of API responses for each uploaded file.
        """
        if not edit_id:
            raise PlayValidationError("edit_id is required")
        if not language:
            raise PlayValidationError("language is required")
        jobs: list[tuple[str, list[str]]] = [
            ("phoneScreenshots", phone_paths or []),
            ("sevenInchScreenshots", tablet7_paths or []),
            ("tenInchScreenshots", tablet10_paths or []),
        ]
        results: dict[str, list[dict]] = {}
        for image_type, paths in jobs:
            if not paths:
                continue
            self.delete_all_images(edit_id, language, image_type)
            uploaded: list[dict] = []
            for path in paths:
                response = self.upload_image(
                    edit_id, language, image_type, path
                )
                uploaded.append(response)
            results[image_type] = uploaded
        return results

    def bulk_update_localized(
        self,
        edit_id: str,
        translations: dict[str, dict[str, Any]],
    ) -> dict[str, dict]:
        """Update listings for many locales in a single pass.

        Args:
            edit_id: Edit identifier returned from edits.insert.
            translations: Mapping of locale to per locale listing fields.
                Each entry must provide title, short_desc, and full_desc.
                An optional video field is forwarded when present.

        Returns:
            A mapping of locale to the updated listing resource.
        """
        if not edit_id:
            raise PlayValidationError("edit_id is required")
        if not isinstance(translations, dict) or not translations:
            raise PlayValidationError(
                "translations must be a non empty dict keyed by locale"
            )
        results: dict[str, dict] = {}
        for locale, fields_map in translations.items():
            if not isinstance(fields_map, dict):
                raise PlayValidationError(
                    "translations[{0}] must be a dict".format(locale)
                )
            title = fields_map.get("title", "")
            short_desc = fields_map.get("short_desc") or fields_map.get(
                "shortDescription", ""
            )
            full_desc = fields_map.get("full_desc") or fields_map.get(
                "fullDescription", ""
            )
            video = fields_map.get("video")
            results[locale] = self.update_listing(
                edit_id,
                locale,
                title,
                short_desc,
                full_desc,
                video=video,
            )
        _LOG.info("bulk_update_localized locales=%d", len(results))
        return results


def _load_translations_file(path: str) -> dict[str, dict[str, Any]]:
    """Load a JSON translations file keyed by locale."""
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise PlayValidationError(
            "translations file not found: {0}".format(file_path)
        )
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PlayValidationError(
            "failed to read translations file {0}: {1}".format(file_path, exc)
        ) from exc
    if not isinstance(data, dict):
        raise PlayValidationError(
            "translations file must contain a JSON object keyed by locale"
        )
    return data


def _main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for listing management."""
    parser = argparse.ArgumentParser(
        prog="publishing.play.listing",
        description="Manage Google Play store listings and image assets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    locales_cmd = subparsers.add_parser(
        "locales", help="Print the target locale list."
    )
    locales_cmd.set_defaults(handler="locales")

    validate_cmd = subparsers.add_parser(
        "validate", help="Validate listing field lengths."
    )
    validate_cmd.add_argument("--title", required=True)
    validate_cmd.add_argument("--short", required=True)
    validate_cmd.add_argument("--full", required=True)
    validate_cmd.set_defaults(handler="validate")

    bulk_cmd = subparsers.add_parser(
        "bulk-update",
        help="Bulk update per locale listings from a JSON translations file.",
    )
    bulk_cmd.add_argument("--edit-id", required=True)
    bulk_cmd.add_argument("--translations", required=True)
    bulk_cmd.set_defaults(handler="bulk-update")

    args = parser.parse_args(argv)

    if args.handler == "locales":
        print(json.dumps(TARGET_LOCALES, indent=2))
        return 0
    if args.handler == "validate":
        ok, message = validate_listing_fields(args.title, args.short, args.full)
        print(json.dumps({"ok": ok, "message": message}, indent=2))
        return 0 if ok else 1
    if args.handler == "bulk-update":
        translations = _load_translations_file(args.translations)
        manager = ListingManager()
        results = manager.bulk_update_localized(args.edit_id, translations)
        print(json.dumps({"updated": sorted(results.keys())}, indent=2))
        return 0
    parser.error("unknown command")
    return 2


__all__ = [
    "FeatureGraphicConfig",
    "FULL_DESCRIPTION_MAX_CHARS",
    "IMAGE_TYPES",
    "IconConfig",
    "ListingManager",
    "MAX_IMAGE_BYTES",
    "MULTI_IMAGE_TYPES",
    "SHORT_DESCRIPTION_MAX_CHARS",
    "TARGET_LOCALES",
    "TITLE_MAX_CHARS",
    "validate_listing_fields",
]


if __name__ == "__main__":
    sys.exit(_main())
