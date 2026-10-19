#!/usr/bin/env bash
#
# test_keepalive.sh
#
# Validates the 7 launchd plists under daemons/launchd/.
#
# Scope:
#   1. Parse each plist as valid XML plist via python3 plistlib.
#   2. Assert required keys: Label, ProgramArguments, RunAtLoad,
#      ThrottleInterval, StandardOutPath, StandardErrorPath.
#   3. Assert ThrottleInterval equals 30.
#   4. Assert Label matches filename.
#   5. Dry run the launchctl load and unload commands. Actually loading a
#      plist has side effects, so by default we only print the commands.
#      Set RUN_LAUNCHCTL=1 to execute.
#   6. Simulated KeepAlive check: spawn short lived Python process, SIGKILL
#      it, observe lifecycle in user space.
#
# Exit 0 on all pass, 1 on any failure.
#
# Usage:
#   bash daemons/test_keepalive.sh
#   RUN_LAUNCHCTL=1 bash daemons/test_keepalive.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_DIR="${SCRIPT_DIR}/launchd"

PLISTS=(
    "com.opencode.orchestrator.plist"
    "com.opencode.watcher.plist"
    "com.opencode.memory-consolidator.plist"
    "com.opencode.telemetry-rollup.plist"
    "com.opencode.release-watcher.plist"
    "com.opencode.crash-fix-loop.plist"
    "com.opencode.marketing-scheduler.plist"
)

PASS=0
FAIL=0
FAILED_TESTS=()

report_pass() {
    printf "[PASS] %s\n" "$1"
    PASS=$((PASS + 1))
}

report_fail() {
    printf "[FAIL] %s: %s\n" "$1" "$2"
    FAIL=$((FAIL + 1))
    FAILED_TESTS+=("$1: $2")
}

validate_plist_xml() {
    local path="$1"
    python3 - "$path" <<'PYEOF'
import plistlib
import sys
path = sys.argv[1]
try:
    with open(path, "rb") as handle:
        data = plistlib.load(handle)
except Exception as exc:
    print(f"parse_error: {exc}", file=sys.stderr)
    sys.exit(2)
required = [
    "Label",
    "ProgramArguments",
    "RunAtLoad",
    "ThrottleInterval",
    "StandardOutPath",
    "StandardErrorPath",
]
missing = [key for key in required if key not in data]
if missing:
    print(f"missing_keys: {missing}", file=sys.stderr)
    sys.exit(3)
if data["ThrottleInterval"] != 30:
    print(f"bad_throttle: {data['ThrottleInterval']}", file=sys.stderr)
    sys.exit(4)
if data["RunAtLoad"] is not True:
    print(f"bad_runatload: {data['RunAtLoad']}", file=sys.stderr)
    sys.exit(5)
if not isinstance(data["ProgramArguments"], list) or not data["ProgramArguments"]:
    print("bad_program_arguments", file=sys.stderr)
    sys.exit(6)
print(data["Label"])
PYEOF
}

check_label_matches_filename() {
    local path="$1"
    local filename
    filename="$(basename "$path" .plist)"
    local label
    label="$(validate_plist_xml "$path" 2>/dev/null || true)"
    if [ "$label" = "$filename" ]; then
        return 0
    fi
    printf "expected Label=%s got=%s" "$filename" "$label"
    return 1
}

check_banned_chars() {
    local path="$1"
    python3 - "$path" <<'PYEOF'
import sys
banned = {0x2012, 0x2013, 0x2014, 0x2015}
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    content = handle.read()
for offset, ch in enumerate(content):
    if ord(ch) in banned:
        print(f"banned_dash U+{ord(ch):04X} at offset {offset}", file=sys.stderr)
        sys.exit(7)
PYEOF
}

dry_run_launchctl() {
    local path="$1"
    local filename
    filename="$(basename "$path")"
    printf "    DRYRUN launchctl bootstrap gui/$(id -u) %s\n" "$path"
    printf "    DRYRUN launchctl bootout gui/$(id -u)/%s\n" "${filename%.plist}"
    if [ "${RUN_LAUNCHCTL:-0}" = "1" ]; then
        launchctl bootstrap "gui/$(id -u)" "$path" || return 1
        sleep 2
        launchctl bootout "gui/$(id -u)/${filename%.plist}" || true
    fi
    return 0
}

simulate_keepalive() {
    local tmp_log
    tmp_log="$(mktemp -t keepalive_sim.XXXXXX)"
    local script
    script="$(mktemp -t keepalive_sim_script.XXXXXX.py)"
    cat >"$script" <<'PYEOF'
import os
import time
with open(os.environ["KEEPALIVE_LOG"], "a") as handle:
    handle.write(f"start pid={os.getpid()}\n")
    handle.flush()
    time.sleep(10)
PYEOF
    KEEPALIVE_LOG="$tmp_log" python3 "$script" >/dev/null 2>&1 &
    local child=$!
    sleep 1
    if ! kill -0 "$child" 2>/dev/null; then
        rm -f "$tmp_log" "$script"
        return 1
    fi
    kill -KILL "$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
    if [ ! -s "$tmp_log" ]; then
        rm -f "$tmp_log" "$script"
        return 1
    fi
    rm -f "$tmp_log" "$script"
    return 0
}

printf "\n== Validating %d plist files ==\n" "${#PLISTS[@]}"
printf "Plist dir: %s\n\n" "$PLIST_DIR"

for plist in "${PLISTS[@]}"; do
    path="${PLIST_DIR}/${plist}"
    printf "\n%s\n" "$plist"
    if [ ! -f "$path" ]; then
        report_fail "$plist" "file not found at $path"
        continue
    fi
    if out="$(validate_plist_xml "$path" 2>&1)"; then
        report_pass "$plist parse and required keys"
    else
        report_fail "$plist" "plist validation failed: $out"
        continue
    fi
    if msg="$(check_label_matches_filename "$path")"; then
        report_pass "$plist Label matches filename"
    else
        report_fail "$plist" "label mismatch: $msg"
    fi
    if check_banned_chars "$path" 2>/dev/null; then
        report_pass "$plist no banned dash characters"
    else
        report_fail "$plist" "banned dash character detected"
    fi
    if dry_run_launchctl "$path"; then
        report_pass "$plist launchctl dry run"
    else
        report_fail "$plist" "launchctl dry run failed"
    fi
done

printf "\n== Simulated KeepAlive check ==\n"
if simulate_keepalive; then
    report_pass "simulated keepalive process lifecycle"
else
    report_fail "simulate_keepalive" "could not start and observe lifecycle"
fi

printf "\n== Summary ==\n"
printf "PASS: %d\n" "$PASS"
printf "FAIL: %d\n" "$FAIL"

if [ "$FAIL" -gt 0 ]; then
    printf "\nFailed tests:\n"
    for entry in "${FAILED_TESTS[@]}"; do
        printf "  %s\n" "$entry"
    done
    exit 1
fi
exit 0
