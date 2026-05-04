"""Google Play Console Chrome automator for API gap surfaces.

This module orchestrates the Play Console UI surfaces that have no
coverage in the monetization or publishing v3 API. It is intended to
be driven by the Claude in Chrome MCP tools while the browser session
is already authenticated by the user (interactive sign in with two
factor auth is handled outside this module).

Surfaces covered
    * App content questionnaire (privacy policy URL, target audience,
      ads declaration, content guidelines, app access / review login).
    * Data Safety form (data types collected and shared, optional vs
      required, security practices such as encryption in transit and
      at rest, data deletion, Play Families declaration).
    * IARC rating questionnaire (thirty plus questions about violence,
      sex, drugs, gambling, UGC, data collection; submits for rating).
    * Production access questionnaire (12 testers confirmed, 14 days
      elapsed of closed testing, real devices used, user feedback).

Design
    The module is a scaffold: in dry run mode it prints the planned
    navigation, click, and fill operations. In live mode the methods
    would dispatch those operations via the Claude in Chrome MCP tool
    family (mcp__claude_in_chrome__navigate, mcp__claude_in_chrome__click,
    mcp__claude_in_chrome__fill, mcp__claude_in_chrome__screenshot).

    Actual MCP wiring is delegated to a thin _mcp_call hook which the
    caller can monkey patch to connect to whichever runtime adapter is
    available (for example, OpenCode task tool, direct MCP stdio, or a
    test double).

External dependencies
    None beyond the Python 3 standard library for this module itself.
    The Claude in Chrome MCP extension must be loaded in the session
    for live mode to succeed.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


_LOG = logging.getLogger("publishing.chrome.automator")
if not _LOG.handlers:
    _LOG.addHandler(logging.NullHandler())


PLAY_CONSOLE_BASE = "https://play.google.com/console"

URL_APP_CONTENT = PLAY_CONSOLE_BASE + "/u/0/developers/{developer_id}/app/{app_id}/app-content"
URL_DATA_SAFETY = PLAY_CONSOLE_BASE + "/u/0/developers/{developer_id}/app/{app_id}/app-content/data-safety"
URL_IARC = PLAY_CONSOLE_BASE + "/u/0/developers/{developer_id}/app/{app_id}/app-content/rating"
URL_PROD_ACCESS = PLAY_CONSOLE_BASE + "/u/0/developers/{developer_id}/app/{app_id}/testing/production-access"

DEFAULT_WAIT_SECONDS = 30
DEFAULT_POLL_INTERVAL = 0.5

SURFACE_APP_CONTENT = "app_content"
SURFACE_DATA_SAFETY = "data_safety"
SURFACE_IARC = "iarc"
SURFACE_PRODUCTION_ACCESS = "production_access"

ALL_SURFACES: tuple[str, ...] = (
    SURFACE_APP_CONTENT,
    SURFACE_DATA_SAFETY,
    SURFACE_IARC,
    SURFACE_PRODUCTION_ACCESS,
)


class ChromeAutomationError(Exception):
    """Raised when an automation step fails or times out."""

    def __init__(
        self,
        message: str,
        surface: Optional[str] = None,
        step: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.surface = surface
        self.step = step
        self.screenshot_path = screenshot_path

    def __str__(self) -> str:
        base = super().__str__()
        parts = [base]
        if self.surface:
            parts.append("surface={0}".format(self.surface))
        if self.step:
            parts.append("step={0}".format(self.step))
        if self.screenshot_path:
            parts.append("screenshot={0}".format(self.screenshot_path))
        return " | ".join(parts)


@dataclass
class AppContentConfig:
    """Inputs required to complete the App content questionnaire."""

    privacy_policy_url: str
    target_age_groups: list[str] = field(default_factory=lambda: ["18+"])
    contains_ads: bool = False
    app_access_restricted: bool = False
    review_username: str = ""
    review_password: str = ""
    content_guidelines_accepted: bool = True
    us_state_laws_accepted: bool = True


@dataclass
class DataSafetyConfig:
    """Inputs required to complete the Data Safety form."""

    data_types_collected: list[str] = field(default_factory=list)
    data_types_shared: list[str] = field(default_factory=list)
    collection_is_optional: bool = True
    encryption_in_transit: bool = True
    can_request_deletion: bool = True
    play_families_compliant: bool = True
    independent_security_review: bool = False
    security_practices_url: str = ""


@dataclass
class IARCAnswers:
    """Answers to the IARC rating questionnaire (30+ items).

    Store answers as a mapping of question identifier to string or bool
    answer. Typical keys include "violence", "sexual_content", "drugs",
    "gambling", "ugc", "location_sharing", etc.
    """

    answers: dict[str, Any] = field(default_factory=dict)
    category: str = "App"
    email: str = ""

    def get(self, key: str, default: Any = None) -> Any:
        return self.answers.get(key, default)


@dataclass
class ProductionAccessConfig:
    """Inputs required to complete production access questionnaire."""

    testers_enrolled: int = 12
    closed_test_days_elapsed: int = 14
    real_devices_used: bool = True
    feedback_addressed: bool = True
    testing_summary: str = "Closed testing with 12 external testers for 14 days."


@dataclass
class AutomationStep:
    """A single step in the automation plan."""

    action: str
    target: str = ""
    value: str = ""
    note: str = ""

    def describe(self) -> str:
        parts = ["action={0}".format(self.action)]
        if self.target:
            parts.append("target={0}".format(self.target))
        if self.value:
            value_preview = self.value if len(self.value) <= 60 else self.value[:57] + "..."
            parts.append("value={0}".format(value_preview))
        if self.note:
            parts.append("note={0}".format(self.note))
        return " ".join(parts)


class PlayConsoleAutomator:
    """Drive Play Console surfaces that lack v3 API coverage.

    The automator is session agnostic: in live mode it uses an MCP hook
    to dispatch navigation and interaction. In dry run mode it records
    the plan and returns it for inspection.
    """

    def __init__(
        self,
        app_id: str,
        developer_id: str = "0",
        mcp_tool_prefix: str = "mcp__claude-in-chrome",
        mcp_hook: Optional[Callable[[str, dict[str, Any]], Any]] = None,
        dry_run: bool = False,
    ) -> None:
        """Initialise the automator.

        Args:
            app_id: Play Console application identifier.
            developer_id: Developer account identifier, typically "0"
                for the primary account under a Google login.
            mcp_tool_prefix: Prefix for Claude in Chrome MCP tool names.
            mcp_hook: Optional callable that accepts a tool name and a
                kwargs dict, and returns whatever the runtime returns.
                When None, dry run mode must be used for successful runs.
            dry_run: When True, record the plan without dispatching.
        """
        if not app_id:
            raise ChromeAutomationError("app_id is required")
        self.app_id = app_id
        self.developer_id = developer_id
        self.mcp_tool_prefix = mcp_tool_prefix
        self.mcp_hook = mcp_hook
        self.dry_run = bool(dry_run)
        self.plan: list[AutomationStep] = []
        self.current_surface: Optional[str] = None

    def _format_url(self, template: str) -> str:
        return template.format(
            developer_id=self.developer_id,
            app_id=self.app_id,
        )

    def _mcp_call(self, tool_suffix: str, kwargs: dict[str, Any]) -> Any:
        """Dispatch an MCP tool call or no op in dry run mode."""
        tool_name = "{0}__{1}".format(self.mcp_tool_prefix, tool_suffix)
        if self.dry_run:
            _LOG.info("dry_run tool=%s args=%s", tool_name, kwargs)
            return {"dry_run": True, "tool": tool_name, "args": kwargs}
        if self.mcp_hook is None:
            raise ChromeAutomationError(
                "mcp_hook is not configured; either enable dry_run or "
                "provide an mcp_hook callable that dispatches MCP tools",
                step=tool_suffix,
            )
        try:
            return self.mcp_hook(tool_name, kwargs)
        except Exception as exc:
            raise ChromeAutomationError(
                "MCP tool {0} failed: {1}".format(tool_name, exc),
                step=tool_suffix,
            ) from exc

    def _record(self, step: AutomationStep) -> None:
        step.note = step.note or (self.current_surface or "")
        self.plan.append(step)
        _LOG.info("plan surface=%s %s", self.current_surface, step.describe())

    def _nav(self, url: str) -> Any:
        self._record(AutomationStep(action="navigate", target=url))
        return self._mcp_call("navigate", {"url": url})

    def _click(self, selector: str) -> Any:
        self._record(AutomationStep(action="click", target=selector))
        return self._mcp_call("click", {"selector": selector})

    def _fill(self, selector: str, value: str) -> Any:
        self._record(AutomationStep(action="fill", target=selector, value=value))
        return self._mcp_call("fill", {"selector": selector, "value": value})

    def _select(self, selector: str, option: str) -> Any:
        self._record(
            AutomationStep(action="select", target=selector, value=option)
        )
        return self._mcp_call(
            "select", {"selector": selector, "option": option}
        )

    def _wait(
        self,
        selector: str,
        timeout: int = DEFAULT_WAIT_SECONDS,
    ) -> Any:
        self._record(
            AutomationStep(
                action="wait",
                target=selector,
                note="timeout={0}s".format(timeout),
            )
        )
        if self.dry_run:
            return {"dry_run": True, "selector": selector}
        result = self._mcp_call(
            "wait_for", {"selector": selector, "timeout_seconds": timeout}
        )
        if result is None:
            raise ChromeAutomationError(
                "wait timed out for {0}".format(selector),
                step="wait",
            )
        return result

    def _screenshot(self, label: str = "") -> str:
        self._record(AutomationStep(action="screenshot", note=label))
        if self.dry_run:
            return "dry_run://screenshot/{0}".format(label or "unlabelled")
        result = self._mcp_call("screenshot", {"label": label})
        if isinstance(result, dict):
            return str(result.get("path") or result.get("url") or "")
        return str(result or "")

    def _submit(self, selector: str) -> Any:
        self._record(AutomationStep(action="submit", target=selector))
        return self._mcp_call("click", {"selector": selector})

    def complete_app_content(self, data: dict) -> dict:
        """Fill the App content questionnaire."""
        self.current_surface = SURFACE_APP_CONTENT
        config = _coerce_app_content(data)
        try:
            self._nav(self._format_url(URL_APP_CONTENT))
            self._wait("[data-surface='app-content']")
            self._click("button[data-track='privacy-policy-edit']")
            self._wait("input[name='privacyPolicyUrl']")
            self._fill("input[name='privacyPolicyUrl']", config.privacy_policy_url)
            self._click("button[type='submit']")
            self._click("button[data-track='ads-declaration-edit']")
            self._select(
                "select[name='hasAds']",
                "true" if config.contains_ads else "false",
            )
            self._click("button[type='submit']")
            self._click("button[data-track='app-access-edit']")
            if config.app_access_restricted:
                self._click("input[name='restricted-access']")
                self._fill("input[name='reviewer-username']", config.review_username)
                self._fill("input[name='reviewer-password']", config.review_password)
            else:
                self._click("input[name='open-access']")
            self._click("button[type='submit']")
            self._click("button[data-track='target-audience-edit']")
            for group in config.target_age_groups:
                self._click(
                    "input[type='checkbox'][data-age-group='{0}']".format(group)
                )
            self._click("button[type='submit']")
            if config.content_guidelines_accepted:
                self._click("input[name='content-guidelines-accept']")
            if config.us_state_laws_accepted:
                self._click("input[name='us-state-laws-accept']")
            self._submit("button[data-action='save-app-content']")
            return {
                "surface": SURFACE_APP_CONTENT,
                "status": "ok",
                "steps": len(self.plan),
                "config": _config_to_dict(config),
            }
        except ChromeAutomationError as exc:
            shot = self._screenshot(label="app_content_error")
            exc.surface = SURFACE_APP_CONTENT
            exc.screenshot_path = shot
            raise
        finally:
            self.current_surface = None

    def complete_data_safety(self, data: dict) -> dict:
        """Fill the Data Safety form."""
        self.current_surface = SURFACE_DATA_SAFETY
        config = _coerce_data_safety(data)
        try:
            self._nav(self._format_url(URL_DATA_SAFETY))
            self._wait("[data-surface='data-safety']")
            self._click("button[data-track='data-collection-edit']")
            self._wait("section[data-section='data-collection']")
            for data_type in config.data_types_collected:
                self._click(
                    "input[type='checkbox'][data-collected='{0}']".format(data_type)
                )
                self._click(
                    "input[name='collection-{0}-optional']".format(data_type)
                    if config.collection_is_optional
                    else "input[name='collection-{0}-required']".format(data_type)
                )
            self._click("button[type='submit']")
            self._click("button[data-track='data-sharing-edit']")
            self._wait("section[data-section='data-sharing']")
            for data_type in config.data_types_shared:
                self._click(
                    "input[type='checkbox'][data-shared='{0}']".format(data_type)
                )
            self._click("button[type='submit']")
            self._click("button[data-track='security-practices-edit']")
            self._wait("section[data-section='security-practices']")
            if config.encryption_in_transit:
                self._click("input[name='encryption-in-transit']")
            if config.can_request_deletion:
                self._click("input[name='deletion-request']")
            if config.independent_security_review:
                self._click("input[name='independent-review']")
            if config.security_practices_url:
                self._fill(
                    "input[name='security-practices-url']",
                    config.security_practices_url,
                )
            self._click("button[type='submit']")
            if config.play_families_compliant:
                self._click("input[name='play-families-compliant']")
            self._submit("button[data-action='save-data-safety']")
            return {
                "surface": SURFACE_DATA_SAFETY,
                "status": "ok",
                "steps": len(self.plan),
                "config": _config_to_dict(config),
            }
        except ChromeAutomationError as exc:
            shot = self._screenshot(label="data_safety_error")
            exc.surface = SURFACE_DATA_SAFETY
            exc.screenshot_path = shot
            raise
        finally:
            self.current_surface = None

    def complete_iarc_questionnaire(self, answers: dict) -> dict:
        """Fill the IARC rating questionnaire."""
        self.current_surface = SURFACE_IARC
        parsed = _coerce_iarc(answers)
        try:
            self._nav(self._format_url(URL_IARC))
            self._wait("[data-surface='iarc-rating']")
            self._click("button[data-track='start-questionnaire']")
            if parsed.email:
                self._fill("input[name='contact-email']", parsed.email)
            self._select("select[name='app-category']", parsed.category)
            self._click("button[type='submit']")
            for question_key, answer in sorted(parsed.answers.items()):
                selector = (
                    "input[name='q-{0}']"
                    "[value='{1}']".format(question_key, _iarc_value(answer))
                )
                self._click(selector)
            self._click("button[data-action='review-answers']")
            self._wait("section[data-section='iarc-review']")
            self._submit("button[data-action='submit-iarc']")
            return {
                "surface": SURFACE_IARC,
                "status": "ok",
                "questions_answered": len(parsed.answers),
                "category": parsed.category,
                "steps": len(self.plan),
            }
        except ChromeAutomationError as exc:
            shot = self._screenshot(label="iarc_error")
            exc.surface = SURFACE_IARC
            exc.screenshot_path = shot
            raise
        finally:
            self.current_surface = None

    def complete_production_access(self, data: dict) -> dict:
        """Fill the production access questionnaire."""
        self.current_surface = SURFACE_PRODUCTION_ACCESS
        config = _coerce_production_access(data)
        try:
            self._nav(self._format_url(URL_PROD_ACCESS))
            self._wait("[data-surface='production-access']")
            if config.testers_enrolled < 12:
                raise ChromeAutomationError(
                    "testers_enrolled must be >= 12 (got {0})".format(
                        config.testers_enrolled
                    ),
                    surface=SURFACE_PRODUCTION_ACCESS,
                    step="validate.testers",
                )
            if config.closed_test_days_elapsed < 14:
                raise ChromeAutomationError(
                    "closed_test_days_elapsed must be >= 14 (got {0})".format(
                        config.closed_test_days_elapsed
                    ),
                    surface=SURFACE_PRODUCTION_ACCESS,
                    step="validate.days",
                )
            self._fill(
                "input[name='testers-count']",
                str(config.testers_enrolled),
            )
            self._fill(
                "input[name='test-days']",
                str(config.closed_test_days_elapsed),
            )
            if config.real_devices_used:
                self._click("input[name='real-devices-used']")
            if config.feedback_addressed:
                self._click("input[name='feedback-addressed']")
            self._fill(
                "textarea[name='testing-summary']",
                config.testing_summary,
            )
            self._submit("button[data-action='submit-production-access']")
            return {
                "surface": SURFACE_PRODUCTION_ACCESS,
                "status": "ok",
                "steps": len(self.plan),
                "config": _config_to_dict(config),
            }
        except ChromeAutomationError as exc:
            shot = self._screenshot(label="production_access_error")
            exc.surface = SURFACE_PRODUCTION_ACCESS
            exc.screenshot_path = shot
            raise
        finally:
            self.current_surface = None

    def run_all_required(self, app_config: dict) -> dict:
        """Run all four required surfaces in sequence."""
        if not isinstance(app_config, dict):
            raise ChromeAutomationError("app_config must be a dict")
        started = time.time()
        results: dict[str, Any] = {}
        errors: list[dict[str, Any]] = []
        for surface in ALL_SURFACES:
            section = app_config.get(surface) or {}
            try:
                if surface == SURFACE_APP_CONTENT:
                    results[surface] = self.complete_app_content(section)
                elif surface == SURFACE_DATA_SAFETY:
                    results[surface] = self.complete_data_safety(section)
                elif surface == SURFACE_IARC:
                    results[surface] = self.complete_iarc_questionnaire(section)
                elif surface == SURFACE_PRODUCTION_ACCESS:
                    results[surface] = self.complete_production_access(section)
            except ChromeAutomationError as exc:
                errors.append(
                    {
                        "surface": exc.surface or surface,
                        "message": str(exc),
                        "step": exc.step,
                        "screenshot": exc.screenshot_path,
                    }
                )
        elapsed = time.time() - started
        return {
            "app_id": self.app_id,
            "dry_run": self.dry_run,
            "elapsed_seconds": round(elapsed, 3),
            "results": results,
            "errors": errors,
            "total_steps": len(self.plan),
        }


def _coerce_app_content(data: dict) -> AppContentConfig:
    if isinstance(data, AppContentConfig):
        return data
    if not isinstance(data, dict):
        raise ChromeAutomationError("app_content data must be a dict")
    privacy_url = str(data.get("privacy_policy_url") or "")
    if not privacy_url:
        raise ChromeAutomationError(
            "privacy_policy_url is required for app content",
            surface=SURFACE_APP_CONTENT,
        )
    return AppContentConfig(
        privacy_policy_url=privacy_url,
        target_age_groups=list(data.get("target_age_groups") or ["18+"]),
        contains_ads=bool(data.get("contains_ads", False)),
        app_access_restricted=bool(data.get("app_access_restricted", False)),
        review_username=str(data.get("review_username") or ""),
        review_password=str(data.get("review_password") or ""),
        content_guidelines_accepted=bool(data.get("content_guidelines_accepted", True)),
        us_state_laws_accepted=bool(data.get("us_state_laws_accepted", True)),
    )


def _coerce_data_safety(data: dict) -> DataSafetyConfig:
    if isinstance(data, DataSafetyConfig):
        return data
    if not isinstance(data, dict):
        raise ChromeAutomationError("data_safety data must be a dict")
    return DataSafetyConfig(
        data_types_collected=list(data.get("data_types_collected") or []),
        data_types_shared=list(data.get("data_types_shared") or []),
        collection_is_optional=bool(data.get("collection_is_optional", True)),
        encryption_in_transit=bool(data.get("encryption_in_transit", True)),
        can_request_deletion=bool(data.get("can_request_deletion", True)),
        play_families_compliant=bool(data.get("play_families_compliant", True)),
        independent_security_review=bool(
            data.get("independent_security_review", False)
        ),
        security_practices_url=str(data.get("security_practices_url") or ""),
    )


def _coerce_iarc(data: dict) -> IARCAnswers:
    if isinstance(data, IARCAnswers):
        return data
    if not isinstance(data, dict):
        raise ChromeAutomationError("iarc answers must be a dict")
    answers_raw = data.get("answers")
    answers: dict[str, Any]
    if isinstance(answers_raw, dict):
        answers = dict(answers_raw)
    else:
        answers = {
            key: value
            for key, value in data.items()
            if key not in {"category", "email"}
        }
    return IARCAnswers(
        answers=answers,
        category=str(data.get("category") or "App"),
        email=str(data.get("email") or ""),
    )


def _coerce_production_access(data: dict) -> ProductionAccessConfig:
    if isinstance(data, ProductionAccessConfig):
        return data
    if not isinstance(data, dict):
        raise ChromeAutomationError("production access data must be a dict")
    return ProductionAccessConfig(
        testers_enrolled=int(data.get("testers_enrolled", 12)),
        closed_test_days_elapsed=int(data.get("closed_test_days_elapsed", 14)),
        real_devices_used=bool(data.get("real_devices_used", True)),
        feedback_addressed=bool(data.get("feedback_addressed", True)),
        testing_summary=str(
            data.get("testing_summary")
            or "Closed testing with 12 external testers for 14 days."
        ),
    )


def _iarc_value(answer: Any) -> str:
    """Map a Python answer to the IARC radio value string."""
    if isinstance(answer, bool):
        return "yes" if answer else "no"
    if answer is None:
        return "no"
    return str(answer)


def _config_to_dict(config: Any) -> dict[str, Any]:
    """Convert a dataclass config to a JSON serialisable dict."""
    if hasattr(config, "__dataclass_fields__"):
        out: dict[str, Any] = {}
        for field_name in config.__dataclass_fields__:
            value = getattr(config, field_name)
            if field_name in {"review_password"}:
                out[field_name] = "***" if value else ""
            else:
                out[field_name] = value
        return out
    if isinstance(config, dict):
        return dict(config)
    return {"value": str(config)}


def _main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for the Chrome automator scaffold."""
    parser = argparse.ArgumentParser(
        prog="publishing.chrome.automator",
        description="Run the Play Console automator for API gap surfaces.",
    )
    parser.add_argument("--app-id", required=True, help="Play Console app id.")
    parser.add_argument(
        "--developer-id",
        default="0",
        help="Developer account id (default: 0).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Record the automation plan without dispatching MCP calls.",
    )
    parser.add_argument(
        "--config",
        required=False,
        default=None,
        help="Path to a JSON config file with per surface inputs.",
    )
    parser.add_argument(
        "--surface",
        required=False,
        default="all",
        choices=list(ALL_SURFACES) + ["all"],
        help="Specific surface to run (or all).",
    )
    args = parser.parse_args(argv)

    app_config: dict[str, Any] = {}
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if not isinstance(loaded, dict):
                raise ChromeAutomationError(
                    "config file must contain a JSON object"
                )
            app_config = loaded
        except (OSError, ValueError) as exc:
            raise ChromeAutomationError(
                "failed to read config {0}: {1}".format(args.config, exc)
            ) from exc

    automator = PlayConsoleAutomator(
        app_id=args.app_id,
        developer_id=args.developer_id,
        dry_run=bool(args.dry_run),
    )

    try:
        if args.surface == "all":
            result = automator.run_all_required(app_config)
        elif args.surface == SURFACE_APP_CONTENT:
            result = automator.complete_app_content(app_config.get(SURFACE_APP_CONTENT) or {})
        elif args.surface == SURFACE_DATA_SAFETY:
            result = automator.complete_data_safety(app_config.get(SURFACE_DATA_SAFETY) or {})
        elif args.surface == SURFACE_IARC:
            result = automator.complete_iarc_questionnaire(
                app_config.get(SURFACE_IARC) or {}
            )
        elif args.surface == SURFACE_PRODUCTION_ACCESS:
            result = automator.complete_production_access(
                app_config.get(SURFACE_PRODUCTION_ACCESS) or {}
            )
        else:
            parser.error("unknown surface")
            return 2
    except ChromeAutomationError as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    plan_summary = [step.describe() for step in automator.plan]
    output = {
        "result": result,
        "plan_steps": len(plan_summary),
        "plan": plan_summary if args.dry_run else plan_summary[:10],
    }
    print(json.dumps(output, indent=2, default=str))
    return 0


__all__ = [
    "ALL_SURFACES",
    "AppContentConfig",
    "AutomationStep",
    "ChromeAutomationError",
    "DEFAULT_POLL_INTERVAL",
    "DEFAULT_WAIT_SECONDS",
    "DataSafetyConfig",
    "IARCAnswers",
    "PLAY_CONSOLE_BASE",
    "PlayConsoleAutomator",
    "ProductionAccessConfig",
    "SURFACE_APP_CONTENT",
    "SURFACE_DATA_SAFETY",
    "SURFACE_IARC",
    "SURFACE_PRODUCTION_ACCESS",
    "URL_APP_CONTENT",
    "URL_DATA_SAFETY",
    "URL_IARC",
    "URL_PROD_ACCESS",
]


if __name__ == "__main__":
    sys.exit(_main())
