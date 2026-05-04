"""Google Play Developer API v3 client.

This module provides a thin wrapper around the Google Play Android Publisher
API v3 for automated release management. It handles service account
authentication, edit lifecycle operations (insert, commit, validate, delete),
retries with exponential backoff, and structured error reporting.

API reference
    Base URL: https://androidpublisher.googleapis.com/androidpublisher/v3/
    Docs:     https://developers.google.com/android-publisher
    Scope:    https://www.googleapis.com/auth/androidpublisher

Authentication
    Uses an OAuth2 service account with the androidpublisher scope.
    The service account JSON file path is read from the environment
    variable GPLAY_SERVICE_ACCOUNT_JSON. The target application package
    name is read from GPLAY_APP_PACKAGE.

External dependencies
    pip install google-api-python-client google-auth

Resource hierarchy
    applications -> edits -> tracks / releases / listings
    Edit workflow: insert edit, modify, then commit or validate.

Log file
    All API call attempts and failures are appended to ~/.opencode/play.log.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

try:
    from google.oauth2 import service_account
    from googleapiclient import discovery
    from googleapiclient.errors import HttpError
    _GOOGLE_LIBS_AVAILABLE = True
    _IMPORT_ERROR_MESSAGE = ""
except ImportError as _exc:
    service_account = None
    discovery = None
    HttpError = Exception
    _GOOGLE_LIBS_AVAILABLE = False
    _IMPORT_ERROR_MESSAGE = (
        "Google API client libraries are not installed. Install them via: "
        "pip install google-api-python-client google-auth. "
        "Original import error: {0}".format(_exc)
    )


PLAY_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
API_NAME = "androidpublisher"
API_VERSION = "v3"

ENV_SERVICE_ACCOUNT = "GPLAY_SERVICE_ACCOUNT_JSON"
ENV_APP_PACKAGE = "GPLAY_APP_PACKAGE"

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_BASE_SECONDS = 1.5
DEFAULT_BACKOFF_CAP_SECONDS = 30.0


class PlayAPIError(Exception):
    """Base exception for all Play API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload

    def __str__(self) -> str:
        base = super().__str__()
        if self.status_code is not None:
            return "[{0}] {1}".format(self.status_code, base)
        return base


class PlayAuthError(PlayAPIError):
    """Raised for 401 or 403 responses and local credential problems."""


class PlayRateLimitError(PlayAPIError):
    """Raised when the API returns 429 after all retry attempts."""


class PlayValidationError(PlayAPIError):
    """Raised when an edit fails validation on the server side."""


def _ensure_log_dir() -> Path:
    """Ensure the ~/.opencode directory exists and return the log path."""
    log_dir = Path.home() / ".opencode"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "play.log"


def _build_logger() -> logging.Logger:
    """Build or return the module-level logger writing to ~/.opencode/play.log."""
    logger = logging.getLogger("publishing.play.client")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    try:
        log_path = _ensure_log_dir()
        handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    except OSError:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


_LOG = _build_logger()


def _parse_http_error(exc: Exception) -> tuple[Optional[int], Any]:
    """Extract status code and parsed payload from a googleapiclient HttpError."""
    status_code: Optional[int] = None
    payload: Any = None
    resp = getattr(exc, "resp", None)
    if resp is not None:
        status = getattr(resp, "status", None)
        if status is not None:
            try:
                status_code = int(status)
            except (TypeError, ValueError):
                status_code = None
    content = getattr(exc, "content", None)
    if content is not None:
        if isinstance(content, bytes):
            try:
                content_text = content.decode("utf-8", errors="replace")
            except (UnicodeDecodeError, AttributeError):
                content_text = str(content)
        else:
            content_text = str(content)
        try:
            payload = json.loads(content_text)
        except (ValueError, TypeError):
            payload = content_text
    return status_code, payload


def _classify_http_error(status_code: Optional[int], payload: Any, message: str) -> PlayAPIError:
    """Map a status code to the appropriate PlayAPIError subclass."""
    if status_code in (401, 403):
        return PlayAuthError(message, status_code=status_code, payload=payload)
    if status_code == 429:
        return PlayRateLimitError(message, status_code=status_code, payload=payload)
    if status_code == 400:
        return PlayValidationError(message, status_code=status_code, payload=payload)
    return PlayAPIError(message, status_code=status_code, payload=payload)


class PlayClient:
    """Google Play Developer API v3 client with retry and structured logging."""

    def __init__(
        self,
        service_account_json_path: Optional[str] = None,
        app_package_name: Optional[str] = None,
    ) -> None:
        """Initialise the client.

        Args:
            service_account_json_path: Path to a Google service account JSON
                file. Defaults to the value of the GPLAY_SERVICE_ACCOUNT_JSON
                environment variable when None.
            app_package_name: Target application package name. Defaults to the
                value of the GPLAY_APP_PACKAGE environment variable when None.
        """
        self.service_account_json_path = (
            service_account_json_path
            if service_account_json_path is not None
            else os.environ.get(ENV_SERVICE_ACCOUNT)
        )
        self.app_package_name = (
            app_package_name
            if app_package_name is not None
            else os.environ.get(ENV_APP_PACKAGE)
        )
        self._service: Any = None
        self._credentials: Any = None
        self.max_attempts = DEFAULT_MAX_ATTEMPTS
        self.backoff_base_seconds = DEFAULT_BACKOFF_BASE_SECONDS
        self.backoff_cap_seconds = DEFAULT_BACKOFF_CAP_SECONDS

    @property
    def service(self) -> Any:
        """Return the cached discovery client, authenticating if necessary."""
        if self._service is None:
            self.authenticate()
        return self._service

    def _require_libs(self) -> None:
        """Raise PlayAuthError if Google API client libraries are missing."""
        if not _GOOGLE_LIBS_AVAILABLE:
            raise PlayAuthError(_IMPORT_ERROR_MESSAGE)

    def _require_package(self) -> str:
        """Return the configured package name or raise if it is missing."""
        if not self.app_package_name:
            raise PlayAuthError(
                "Application package name is not configured. Set "
                "GPLAY_APP_PACKAGE or pass app_package_name to PlayClient."
            )
        return self.app_package_name

    def authenticate(self) -> Any:
        """Load service account credentials and build the API service."""
        self._require_libs()
        if not self.service_account_json_path:
            raise PlayAuthError(
                "Service account JSON path is not configured. Set "
                "GPLAY_SERVICE_ACCOUNT_JSON or pass service_account_json_path."
            )
        sa_path = Path(self.service_account_json_path).expanduser()
        if not sa_path.is_file():
            raise PlayAuthError(
                "Service account JSON file not found: {0}".format(sa_path)
            )
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(sa_path), scopes=[PLAY_SCOPE]
            )
        except (ValueError, OSError) as exc:
            raise PlayAuthError(
                "Failed to load service account credentials: {0}".format(exc)
            ) from exc
        try:
            self._service = discovery.build(
                API_NAME,
                API_VERSION,
                credentials=credentials,
                cache_discovery=False,
            )
        except Exception as exc:
            raise PlayAuthError(
                "Failed to build androidpublisher service: {0}".format(exc)
            ) from exc
        self._credentials = credentials
        _LOG.info("authenticate ok sa=%s package=%s", sa_path.name, self.app_package_name)
        return self._service

    def execute(self, request: Any, *, operation: str = "execute") -> Any:
        """Execute an API request with retry and exponential backoff.

        Args:
            request: A prepared googleapiclient request object supporting
                `.execute()`.
            operation: Human readable operation label for logs.

        Returns:
            The decoded JSON body returned by the API.

        Raises:
            PlayAuthError, PlayRateLimitError, PlayValidationError, or
            PlayAPIError depending on the failure mode.
        """
        if request is None:
            raise PlayAPIError("Request object is None for operation: {0}".format(operation))

        attempt = 0
        last_exc: Optional[PlayAPIError] = None
        while attempt < self.max_attempts:
            attempt += 1
            try:
                result = request.execute()
                _LOG.info("op=%s attempt=%d status=ok", operation, attempt)
                return result
            except HttpError as exc:
                status_code, payload = _parse_http_error(exc)
                message = "HTTP {0} during {1}: {2}".format(
                    status_code if status_code is not None else "?", operation, exc
                )
                _LOG.warning(
                    "op=%s attempt=%d status=%s payload=%s",
                    operation,
                    attempt,
                    status_code,
                    payload,
                )
                err = _classify_http_error(status_code, payload, message)
                last_exc = err
                retriable = status_code in (429, 500, 502, 503, 504)
                if not retriable or attempt >= self.max_attempts:
                    raise err from exc
                sleep_for = self._compute_backoff(attempt)
                _LOG.info(
                    "op=%s attempt=%d retry_in=%.2fs",
                    operation,
                    attempt,
                    sleep_for,
                )
                time.sleep(sleep_for)
            except Exception as exc:
                message = "Unexpected error during {0}: {1}".format(operation, exc)
                _LOG.error("op=%s attempt=%d fatal=%s", operation, attempt, exc)
                raise PlayAPIError(message) from exc
        if last_exc is not None:
            raise last_exc
        raise PlayAPIError(
            "Operation {0} failed after {1} attempts".format(operation, self.max_attempts)
        )

    def _compute_backoff(self, attempt: int) -> float:
        """Return an exponential backoff delay with jitter."""
        delay = self.backoff_base_seconds * (2 ** (attempt - 1))
        capped = min(delay, self.backoff_cap_seconds)
        jitter = random.uniform(0.0, capped * 0.25)
        return capped + jitter

    def edits_insert(self) -> dict:
        """Create a new edit and return the edit resource."""
        self._require_libs()
        package = self._require_package()
        request = self.service.edits().insert(packageName=package, body={})
        result = self.execute(request, operation="edits.insert")
        _LOG.info(
            "edits.insert package=%s id=%s expires=%s",
            package,
            result.get("id") if isinstance(result, dict) else None,
            result.get("expiryTimeSeconds") if isinstance(result, dict) else None,
        )
        return result

    def edits_commit(self, edit_id: str, validate_only: bool = False) -> dict:
        """Commit or validate an edit.

        Args:
            edit_id: The edit identifier returned from edits_insert.
            validate_only: When True, only validate the edit without
                committing.
        """
        self._require_libs()
        package = self._require_package()
        if not edit_id:
            raise PlayValidationError("edit_id is required for edits_commit")
        request = self.service.edits().commit(
            packageName=package,
            editId=edit_id,
            validateOnly=bool(validate_only),
        )
        op = "edits.commit.validate_only" if validate_only else "edits.commit"
        return self.execute(request, operation=op)

    def edits_delete(self, edit_id: str) -> None:
        """Abandon an in-progress edit."""
        self._require_libs()
        package = self._require_package()
        if not edit_id:
            raise PlayValidationError("edit_id is required for edits_delete")
        request = self.service.edits().delete(packageName=package, editId=edit_id)
        self.execute(request, operation="edits.delete")
        _LOG.info("edits.delete package=%s id=%s", package, edit_id)

    def edits_validate(self, edit_id: str) -> dict:
        """Validate an edit without committing it (dry run)."""
        self._require_libs()
        package = self._require_package()
        if not edit_id:
            raise PlayValidationError("edit_id is required for edits_validate")
        request = self.service.edits().validate(packageName=package, editId=edit_id)
        return self.execute(request, operation="edits.validate")

    def edits_get(self, edit_id: str) -> dict:
        """Return the current state of an edit."""
        self._require_libs()
        package = self._require_package()
        if not edit_id:
            raise PlayValidationError("edit_id is required for edits_get")
        request = self.service.edits().get(packageName=package, editId=edit_id)
        return self.execute(request, operation="edits.get")


_DEFAULT_CLIENT: Optional[PlayClient] = None


def get_default_client() -> PlayClient:
    """Return a module-level singleton PlayClient built from env vars."""
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = PlayClient()
    return _DEFAULT_CLIENT


__all__ = [
    "PlayAPIError",
    "PlayAuthError",
    "PlayClient",
    "PlayRateLimitError",
    "PlayValidationError",
    "PLAY_SCOPE",
    "API_NAME",
    "API_VERSION",
    "ENV_APP_PACKAGE",
    "ENV_SERVICE_ACCOUNT",
    "get_default_client",
]
