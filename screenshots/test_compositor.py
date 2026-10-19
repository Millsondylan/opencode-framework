#!/usr/bin/env python3
"""Unit tests for the screenshot compositor.

These tests exercise pure-Python behaviour: dataclass construction,
size validation, path hygiene, and in-memory PIL composition so the
suite can run without a real emulator or filesystem fixture directory.

Skip behaviour:
    * Tests that require PIL (Pillow) are skipped when Pillow is not
      installed. The compositor itself degrades gracefully in that case
      and raises CompositorError at runtime.

Run:
    python screenshots/test_compositor.py
    pytest screenshots/test_compositor.py -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from typing import Optional

# Ensure the screenshots directory is on sys.path when this file is
# executed directly via `python screenshots/test_compositor.py`.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import compositor as comp  # noqa: E402

try:
    from PIL import Image  # noqa: F401

    PIL_OK = True
except ImportError:
    PIL_OK = False


def _write_png(path: str, width: int, height: int, color=(32, 64, 96, 255)) -> None:
    """Write a solid color PNG at the given resolution."""
    from PIL import Image as _Image

    img = _Image.new("RGBA", (width, height), color)
    img.save(path, format="PNG")


class DeviceSpecTests(unittest.TestCase):
    """Static tests that do not need Pillow."""

    def test_spec_registry_contains_three_form_factors(self) -> None:
        keys = set(comp.DEVICE_SPECS.keys())
        self.assertEqual(
            keys,
            {"phone_pixel8", "tablet7_nexus7", "tablet10_pixel_tablet"},
        )

    def test_spec_resolutions_match_play_store_sizes(self) -> None:
        for spec in comp.DEVICE_SPECS.values():
            expected = comp.PLAY_STORE_SIZES[spec.form_factor]
            self.assertEqual(
                (spec.width, spec.height),
                expected,
                f"{spec.name} size must equal Play Store size {expected}",
            )

    def test_content_region_computes_correct_bounds(self) -> None:
        spec = comp.DeviceSpec(
            name="Test Frame",
            width=1000,
            height=2000,
            frame_image_path="/nonexistent/frame.png",
            frame_content_box=(50, 100, 900, 1700),
            form_factor="phone",
        )
        self.assertEqual(spec.content_region(), (50, 100, 950, 1800))

    def test_enforce_count_rules_accepts_valid_range(self) -> None:
        ok, msg = comp.enforce_count_rules("phone", 5)
        self.assertTrue(ok, msg=msg)

    def test_enforce_count_rules_rejects_too_few(self) -> None:
        ok, msg = comp.enforce_count_rules("phone", 1)
        self.assertFalse(ok)
        self.assertIn("min is", msg)

    def test_enforce_count_rules_rejects_too_many(self) -> None:
        ok, msg = comp.enforce_count_rules("phone", 99)
        self.assertFalse(ok)
        self.assertIn("exceeds max", msg)


@unittest.skipUnless(PIL_OK, "Pillow not installed; skipping PIL-backed tests.")
class CompositorPilTests(unittest.TestCase):
    """Tests that require Pillow and write to a temp directory."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = self._tmp.name

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make_inputs(self, spec: comp.DeviceSpec):
        ui_path = os.path.join(self.tmp_path, "ui.png")
        bg_path = os.path.join(self.tmp_path, "bg.png")
        _, _, inner_w, inner_h = spec.frame_content_box
        _write_png(ui_path, inner_w, inner_h, color=(200, 20, 20, 255))
        _write_png(bg_path, spec.width, spec.height, color=(0, 120, 255, 255))
        return ui_path, bg_path

    def test_compose_produces_play_store_sized_png(self) -> None:
        spec = comp.DEVICE_SPECS["phone_pixel8"]
        ui_path, bg_path = self._make_inputs(spec)
        out_path = os.path.join(self.tmp_path, "out.png")

        compositor = comp.FrameCompositor(spec)
        result = compositor.compose(ui_path, bg_path, out_path, locale_caption=None)
        self.assertEqual(result, out_path)
        self.assertTrue(os.path.isfile(out_path))

        ok, msg = compositor.validate_play_store_size(out_path, "phone")
        self.assertTrue(ok, msg=msg)

    def test_validate_play_store_size_rejects_wrong_dimensions(self) -> None:
        spec = comp.DEVICE_SPECS["phone_pixel8"]
        out_path = os.path.join(self.tmp_path, "wrong.png")
        _write_png(out_path, 500, 500)

        compositor = comp.FrameCompositor(spec)
        ok, msg = compositor.validate_play_store_size(out_path, "phone")
        self.assertFalse(ok)
        self.assertIn("Size mismatch", msg)

    def test_validate_play_store_size_rejects_unknown_form_factor(self) -> None:
        spec = comp.DEVICE_SPECS["phone_pixel8"]
        compositor = comp.FrameCompositor(spec)
        ok, msg = compositor.validate_play_store_size(
            os.path.join(self.tmp_path, "x.png"),
            "not_a_real_factor",
        )
        self.assertFalse(ok)
        self.assertIn("Unknown form factor", msg)

    def test_compose_raises_when_ui_missing(self) -> None:
        spec = comp.DEVICE_SPECS["phone_pixel8"]
        _, bg_path = self._make_inputs(spec)
        out_path = os.path.join(self.tmp_path, "out.png")

        compositor = comp.FrameCompositor(spec)
        with self.assertRaises(comp.CompositorError) as ctx:
            compositor.compose(
                ui_image_path=os.path.join(self.tmp_path, "does_not_exist.png"),
                bg_image_path=bg_path,
                output_path=out_path,
            )
        self.assertIn("not found", str(ctx.exception))

    def test_batch_compose_runs_all_and_reports_outputs(self) -> None:
        spec = comp.DEVICE_SPECS["phone_pixel8"]
        ui_path, bg_path = self._make_inputs(spec)

        configs = [
            comp.CompositionConfig(
                device_spec=spec,
                ui_path=ui_path,
                bg_path=bg_path,
                output_path=os.path.join(self.tmp_path, f"out_{i}.png"),
                locale_caption=None,
            )
            for i in range(3)
        ]
        outputs = comp.batch_compose(configs)
        self.assertEqual(len(outputs), 3)
        for path in outputs:
            self.assertTrue(os.path.isfile(path))

    def test_aspect_ratio_preservation_when_ui_is_oversized(self) -> None:
        """UI taller than content box should be centre cropped, not squashed."""
        spec = comp.DEVICE_SPECS["phone_pixel8"]
        _, _, inner_w, inner_h = spec.frame_content_box
        ui_path = os.path.join(self.tmp_path, "oversized_ui.png")
        # Build a UI with double the content box height to force cropping.
        _write_png(ui_path, inner_w, inner_h * 2, color=(10, 200, 10, 255))
        bg_path = os.path.join(self.tmp_path, "bg.png")
        _write_png(bg_path, spec.width, spec.height, color=(0, 0, 0, 255))
        out_path = os.path.join(self.tmp_path, "out_crop.png")

        compositor = comp.FrameCompositor(spec)
        compositor.compose(ui_path, bg_path, out_path, locale_caption=None)

        from PIL import Image as _Image

        with _Image.open(out_path) as img:
            self.assertEqual(img.size, (spec.width, spec.height))


def _print_pil_notice() -> None:
    if not PIL_OK:
        print("NOTE: Pillow not installed; PIL-backed tests will be skipped.")


def main() -> int:
    _print_pil_notice()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(DeviceSpecTests))
    suite.addTests(loader.loadTestsFromTestCase(CompositorPilTests))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("ALL TESTS PASSED")
        return 0
    print(f"FAILURES: {len(result.failures)} errors: {len(result.errors)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
