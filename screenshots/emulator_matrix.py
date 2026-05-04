#!/usr/bin/env python3
"""Android emulator matrix driver for Play Store golden captures.

This module orchestrates the three Android Virtual Devices (AVDs) that
produce real UI screenshots for the compositor pipeline:

    1. phone_pixel8:   Pixel 8 (1080x2400 logical, phone form factor)
    2. tablet7_nexus7: Nexus 7 (1200x1920 logical, 7 inch tablet)
    3. tablet10_pixel: Pixel Tablet (1600x2560 logical, 10 inch tablet)

For every AVD the runner boots the emulator, waits for boot_completed,
invokes the matching Flutter integration_test flow from
`screenshots/flows/`, pulls the captured PNG files off the device, and
shuts the emulator down. The images produced here are the ONLY permitted
source of UI pixels for `compositor.py`.

Usage (library):
    runner = EmulatorRunner(AVD_CONFIGS["phone_pixel8"])
    runner.boot()
    runner.wait_boot()
    runner.run_integration_test("integration_test/phone_flow.dart")
    runner.pull_screenshots("captures/phone")
    runner.shutdown()

Usage (CLI):
    python emulator_matrix.py --matrix
    python emulator_matrix.py --only phone_pixel8
    python emulator_matrix.py --dry-run --matrix
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# Default timeouts in seconds. Tuned for M1 hardware; CI may need longer.
BOOT_TIMEOUT_SECONDS = 240
TEST_TIMEOUT_SECONDS = 900
PULL_TIMEOUT_SECONDS = 180
SHUTDOWN_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class AvdConfig:
    """Single AVD descriptor for the capture matrix."""

    key: str
    avd_name: str
    form_factor: str
    flow_path: str
    remote_screenshot_dir: str
    # Optional emulator flags, e.g. window size, language, skin.
    extra_emulator_args: Tuple[str, ...] = field(default_factory=tuple)


AVD_CONFIGS: Dict[str, AvdConfig] = {
    "phone_pixel8": AvdConfig(
        key="phone_pixel8",
        avd_name="Pixel_8_API_34",
        form_factor="phone",
        flow_path="screenshots/flows/phone_flow.dart",
        remote_screenshot_dir="/sdcard/Pictures/flutter_goldens",
        extra_emulator_args=("-no-audio", "-no-boot-anim"),
    ),
    "tablet7_nexus7": AvdConfig(
        key="tablet7_nexus7",
        avd_name="Nexus_7_API_34",
        form_factor="tablet7",
        flow_path="screenshots/flows/tablet7_flow.dart",
        remote_screenshot_dir="/sdcard/Pictures/flutter_goldens",
        extra_emulator_args=("-no-audio", "-no-boot-anim"),
    ),
    "tablet10_pixel_tablet": AvdConfig(
        key="tablet10_pixel_tablet",
        avd_name="Pixel_Tablet_API_34",
        form_factor="tablet10",
        flow_path="screenshots/flows/tablet10_flow.dart",
        remote_screenshot_dir="/sdcard/Pictures/flutter_goldens",
        extra_emulator_args=("-no-audio", "-no-boot-anim"),
    ),
}


class EmulatorError(RuntimeError):
    """Raised when an AVD or adb step fails."""


def _run(
    argv: Sequence[str],
    timeout: int,
    dry_run: bool,
    capture: bool = False,
) -> Tuple[int, str, str]:
    """Run a subprocess, honouring dry-run mode."""
    printable = " ".join(shlex.quote(a) for a in argv)
    if dry_run:
        print(f"[dry-run] {printable}")
        return (0, "", "")
    try:
        proc = subprocess.run(
            list(argv),
            check=False,
            timeout=timeout,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
        )
    except FileNotFoundError as exc:
        raise EmulatorError(
            f"Command not found: {argv[0]}. Install Android SDK platform tools."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise EmulatorError(
            f"Command timed out after {timeout}s: {printable}"
        ) from exc
    return (
        proc.returncode,
        proc.stdout or "",
        proc.stderr or "",
    )


class EmulatorRunner:
    """Drive a single AVD through boot, test, pull, and shutdown."""

    def __init__(self, config: AvdConfig, dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self._emulator_proc: Optional[subprocess.Popen] = None

    def boot(self) -> None:
        """Launch the emulator process in the background."""
        argv = [
            "emulator",
            "-avd",
            self.config.avd_name,
        ] + list(self.config.extra_emulator_args)
        printable = " ".join(shlex.quote(a) for a in argv)
        if self.dry_run:
            print(f"[dry-run] spawn: {printable}")
            return
        try:
            self._emulator_proc = subprocess.Popen(
                argv,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise EmulatorError(
                "emulator binary missing. Add $ANDROID_HOME/emulator to PATH."
            ) from exc
        print(f"Booting {self.config.avd_name} (pid {self._emulator_proc.pid})")

    def wait_boot(self, timeout: int = BOOT_TIMEOUT_SECONDS) -> None:
        """Poll adb until sys.boot_completed is 1."""
        if self.dry_run:
            print(f"[dry-run] wait_boot {self.config.avd_name}")
            return
        deadline = time.time() + timeout
        while time.time() < deadline:
            rc, out, _ = _run(
                ["adb", "shell", "getprop", "sys.boot_completed"],
                timeout=15,
                dry_run=False,
                capture=True,
            )
            if rc == 0 and out.strip() == "1":
                # Give the launcher a moment to settle.
                time.sleep(4)
                print(f"Boot complete: {self.config.avd_name}")
                return
            time.sleep(3)
        raise EmulatorError(
            f"Boot timeout ({timeout}s) on {self.config.avd_name}"
        )

    def run_integration_test(
        self,
        flow_path: Optional[str] = None,
        timeout: int = TEST_TIMEOUT_SECONDS,
    ) -> None:
        """Invoke the Flutter integration_test target on the running AVD."""
        target = flow_path or self.config.flow_path
        if not target:
            raise EmulatorError("No flow_path configured for this AVD")
        argv = [
            "flutter",
            "test",
            target,
            "--dart-define",
            f"SCREENSHOT_FORM_FACTOR={self.config.form_factor}",
        ]
        rc, _, err = _run(argv, timeout=timeout, dry_run=self.dry_run, capture=True)
        if rc != 0:
            raise EmulatorError(
                f"flutter test failed on {self.config.avd_name} "
                f"(rc={rc}): {err.strip()[:400]}"
            )
        print(f"Tests passed on {self.config.avd_name}")

    def pull_screenshots(
        self,
        local_dir: str,
        remote_dir: Optional[str] = None,
    ) -> List[str]:
        """Copy every captured PNG from the device to a local directory."""
        src = remote_dir or self.config.remote_screenshot_dir
        if not self.dry_run:
            os.makedirs(local_dir, exist_ok=True)
        argv = ["adb", "pull", src, local_dir]
        rc, _, err = _run(
            argv,
            timeout=PULL_TIMEOUT_SECONDS,
            dry_run=self.dry_run,
            capture=True,
        )
        if rc != 0:
            raise EmulatorError(
                f"adb pull failed (rc={rc}): {err.strip()[:300]}"
            )
        if self.dry_run:
            return []
        pulled: List[str] = []
        for root, _dirs, files in os.walk(local_dir):
            for name in files:
                if name.lower().endswith(".png"):
                    pulled.append(os.path.join(root, name))
        pulled.sort()
        print(f"Pulled {len(pulled)} PNGs into {local_dir}")
        return pulled

    def shutdown(self, timeout: int = SHUTDOWN_TIMEOUT_SECONDS) -> None:
        """Stop the emulator gracefully, then hard kill if needed."""
        if self.dry_run:
            print(f"[dry-run] shutdown {self.config.avd_name}")
            return
        rc, _, _ = _run(
            ["adb", "emu", "kill"],
            timeout=15,
            dry_run=False,
            capture=True,
        )
        if rc != 0:
            print(f"adb emu kill returned {rc}; falling back to SIGTERM")
        if self._emulator_proc is not None:
            try:
                self._emulator_proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._emulator_proc.terminate()
                try:
                    self._emulator_proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._emulator_proc.kill()
            self._emulator_proc = None
        print(f"Shutdown complete: {self.config.avd_name}")


def run_matrix(
    configs: Iterable[AvdConfig],
    captures_root: str = "captures",
    dry_run: bool = False,
) -> Dict[str, List[str]]:
    """Run every AVD in the matrix sequentially and return pulled files."""
    results: Dict[str, List[str]] = {}
    errors: List[str] = []
    for cfg in configs:
        runner = EmulatorRunner(cfg, dry_run=dry_run)
        local_dir = os.path.join(captures_root, cfg.key)
        try:
            runner.boot()
            runner.wait_boot()
            runner.run_integration_test()
            pulled = runner.pull_screenshots(local_dir)
            results[cfg.key] = pulled
        except EmulatorError as exc:
            errors.append(f"{cfg.key}: {exc}")
            results[cfg.key] = []
        finally:
            try:
                runner.shutdown()
            except EmulatorError as exc:
                errors.append(f"{cfg.key} shutdown: {exc}")
    if errors:
        joined = "; ".join(errors)
        raise EmulatorError(
            f"run_matrix completed with {len(errors)} failures: {joined}"
        )
    return results


def _select_configs(only: Optional[str]) -> List[AvdConfig]:
    if only is None:
        return list(AVD_CONFIGS.values())
    if only not in AVD_CONFIGS:
        raise EmulatorError(
            f"Unknown AVD key '{only}'. Known: {sorted(AVD_CONFIGS.keys())}"
        )
    return [AVD_CONFIGS[only]]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Android emulator golden capture matrix."
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Run all configured AVDs in sequence.",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Run a single AVD by key (see AVD_CONFIGS).",
    )
    parser.add_argument(
        "--captures-root",
        default="captures",
        help="Local directory that receives per AVD subfolders of PNGs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    ns = parser.parse_args(argv)

    if not ns.matrix and ns.only is None:
        parser.error("Specify --matrix or --only <key>.")

    try:
        configs = _select_configs(ns.only)
        results = run_matrix(
            configs,
            captures_root=ns.captures_root,
            dry_run=ns.dry_run,
        )
    except EmulatorError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    total = sum(len(v) for v in results.values())
    print(f"Matrix complete: {total} PNGs across {len(results)} AVDs")
    for key, files in results.items():
        print(f"  {key}: {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
