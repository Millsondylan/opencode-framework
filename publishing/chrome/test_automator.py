"""Dry-run test for the Play Console Chrome automator.

This test exercises the four surfaces covered by PlayConsoleAutomator in
dry run mode. It validates that each surface produces a non empty plan,
that generated selectors are non empty strings, and that no MCP calls are
actually dispatched when dry_run=True.

Run this directly to see PASS/FAIL for each test, or call run_all_tests()
to get a (passed, failed) tuple. Exits with status 0 on full success and
1 on any failure.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


from publishing.chrome.automator import (  # noqa: E402
    ALL_SURFACES,
    AutomationStep,
    PlayConsoleAutomator,
    SURFACE_APP_CONTENT,
    SURFACE_DATA_SAFETY,
    SURFACE_IARC,
    SURFACE_PRODUCTION_ACCESS,
)


def _sample_app_content() -> dict:
    return {
        "privacy_policy_url": "https://example.com/privacy",
        "target_age_groups": ["18+"],
        "contains_ads": False,
        "app_access_restricted": True,
        "review_username": "reviewer@example.com",
        "review_password": "review-password-abcd",
        "content_guidelines_accepted": True,
        "us_state_laws_accepted": True,
    }


def _sample_data_safety() -> dict:
    return {
        "data_types_collected": ["email_address", "app_interactions"],
        "data_types_shared": [],
        "collection_is_optional": True,
        "encryption_in_transit": True,
        "can_request_deletion": True,
        "play_families_compliant": True,
        "independent_security_review": False,
        "security_practices_url": "https://example.com/security",
    }


def _sample_iarc() -> dict:
    base_questions = {
        "violence": "no",
        "sexual_content": "no",
        "drugs": "no",
        "gambling": "no",
        "ugc": "no",
        "location_sharing": "no",
        "profanity": "no",
        "controlled_substances": "no",
        "crude_humor": "no",
        "fear": "no",
        "discrimination": "no",
    }
    return {
        "category": "App",
        "email": "compliance@example.com",
        "answers": base_questions,
    }


def _sample_production_access() -> dict:
    return {
        "testers_enrolled": 12,
        "closed_test_days_elapsed": 14,
        "real_devices_used": True,
        "feedback_addressed": True,
        "testing_summary": "Twelve external testers ran the closed test for fourteen days.",
    }


def _sample_full_config() -> dict:
    return {
        SURFACE_APP_CONTENT: _sample_app_content(),
        SURFACE_DATA_SAFETY: _sample_data_safety(),
        SURFACE_IARC: _sample_iarc(),
        SURFACE_PRODUCTION_ACCESS: _sample_production_access(),
    }


def _new_automator(dry_run: bool = True) -> PlayConsoleAutomator:
    return PlayConsoleAutomator(
        app_id="fake_app_id",
        developer_id="0",
        dry_run=dry_run,
    )


def test_app_content_plan_generated() -> None:
    """complete_app_content(dry_run=True) should produce a plan with steps."""
    automator = _new_automator()
    result = automator.complete_app_content(_sample_app_content())
    assert isinstance(result, dict), "result must be a dict"
    assert result.get("surface") == SURFACE_APP_CONTENT, "wrong surface"
    assert result.get("steps", 0) > 0, "steps count should be positive"
    assert len(automator.plan) > 0, "plan should not be empty"
    surfaces = {step.note for step in automator.plan if step.note}
    assert SURFACE_APP_CONTENT in surfaces, (
        "app_content surface should appear in plan notes: {0}".format(surfaces)
    )


def test_data_safety_plan() -> None:
    """complete_data_safety(dry_run=True) should produce a plan with steps."""
    automator = _new_automator()
    result = automator.complete_data_safety(_sample_data_safety())
    assert isinstance(result, dict), "result must be a dict"
    assert result.get("surface") == SURFACE_DATA_SAFETY, "wrong surface"
    assert result.get("steps", 0) > 0, "steps count should be positive"
    fill_steps = [s for s in automator.plan if s.action == "fill"]
    click_steps = [s for s in automator.plan if s.action == "click"]
    assert len(click_steps) > 0, "data safety flow should produce click steps"
    urls_touched = [s.target for s in fill_steps if "security-practices-url" in s.target]
    assert urls_touched, "security practices url should be filled in sample"


def test_iarc_questionnaire_plan() -> None:
    """IARC flow should generate at least 10 question click steps."""
    automator = _new_automator()
    result = automator.complete_iarc_questionnaire(_sample_iarc())
    assert isinstance(result, dict), "result must be a dict"
    assert result.get("surface") == SURFACE_IARC, "wrong surface"
    question_clicks = [
        s for s in automator.plan
        if s.action == "click" and "q-" in s.target
    ]
    assert len(question_clicks) >= 10, (
        "expected >=10 IARC question clicks, got {0}".format(len(question_clicks))
    )


def test_production_access_plan() -> None:
    """Production access plan should reference testers and days."""
    automator = _new_automator()
    result = automator.complete_production_access(_sample_production_access())
    assert isinstance(result, dict)
    assert result.get("surface") == SURFACE_PRODUCTION_ACCESS
    fill_targets = [s.target for s in automator.plan if s.action == "fill"]
    fill_values = [s.value for s in automator.plan if s.action == "fill"]
    assert any("testers-count" in t for t in fill_targets), (
        "testers-count fill missing: {0}".format(fill_targets)
    )
    assert any("test-days" in t for t in fill_targets), (
        "test-days fill missing: {0}".format(fill_targets)
    )
    assert "12" in fill_values, "testers count value 12 not in fills: {0}".format(fill_values)
    assert "14" in fill_values, "days value 14 not in fills: {0}".format(fill_values)


def test_run_all_required_sequences_all_four() -> None:
    """run_all_required(dry_run=True) should touch all four surfaces."""
    automator = _new_automator()
    summary = automator.run_all_required(_sample_full_config())
    assert isinstance(summary, dict), "summary must be dict"
    assert summary.get("dry_run") is True, "dry_run flag should propagate"
    results = summary.get("results") or {}
    for surface in ALL_SURFACES:
        assert surface in results, (
            "surface {0} missing from run_all_required results".format(surface)
        )
    assert summary.get("total_steps", 0) > 0, "total_steps should be positive"
    errors = summary.get("errors") or []
    assert errors == [], "no errors expected for valid config: {0}".format(errors)


def test_selector_strings_are_non_empty() -> None:
    """Every non screenshot step in the plan must have a non empty selector."""
    automator = _new_automator()
    automator.run_all_required(_sample_full_config())
    action_needs_target = {"click", "fill", "select", "wait", "submit", "navigate"}
    for index, step in enumerate(automator.plan):
        assert isinstance(step, AutomationStep), "plan entry not AutomationStep"
        if step.action in action_needs_target:
            assert step.target and isinstance(step.target, str), (
                "step {0} action={1} has empty target".format(index, step.action)
            )


def test_dry_run_does_not_call_mcp() -> None:
    """With dry_run=True, a mock mcp_hook must never be called."""
    invocations: list[tuple[str, dict[str, Any]]] = []

    def mock_hook(tool_name: str, kwargs: dict[str, Any]) -> Any:
        invocations.append((tool_name, kwargs))
        return {"never_called": True}

    automator = PlayConsoleAutomator(
        app_id="fake_app_id",
        developer_id="0",
        mcp_hook=mock_hook,
        dry_run=True,
    )
    automator.run_all_required(_sample_full_config())
    assert invocations == [], (
        "mcp_hook must not be invoked in dry_run mode; got {0} calls".format(
            len(invocations)
        )
    )


def _run_one(name: str, fn: Any) -> bool:
    """Run one test function, printing PASS or FAIL and returning bool."""
    try:
        fn()
    except AssertionError as exc:
        print("FAIL {0}: {1}".format(name, exc))
        return False
    except Exception as exc:
        print("FAIL {0}: unexpected {1}".format(name, exc))
        traceback.print_exc()
        return False
    print("PASS {0}".format(name))
    return True


def run_all_tests() -> tuple[int, int]:
    """Run every test_ function in this module. Return (passed, failed)."""
    cases = [
        ("test_app_content_plan_generated", test_app_content_plan_generated),
        ("test_data_safety_plan", test_data_safety_plan),
        ("test_iarc_questionnaire_plan", test_iarc_questionnaire_plan),
        ("test_production_access_plan", test_production_access_plan),
        ("test_run_all_required_sequences_all_four", test_run_all_required_sequences_all_four),
        ("test_selector_strings_are_non_empty", test_selector_strings_are_non_empty),
        ("test_dry_run_does_not_call_mcp", test_dry_run_does_not_call_mcp),
    ]
    passed = 0
    failed = 0
    for name, fn in cases:
        if _run_one(name, fn):
            passed += 1
        else:
            failed += 1
    return passed, failed


if __name__ == "__main__":
    p, f = run_all_tests()
    total = p + f
    print("{0}/{1} PASSED".format(p, total))
    sys.exit(0 if f == 0 else 1)
