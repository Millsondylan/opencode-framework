#!/usr/bin/env bash
# verify-alibaba-fix.sh
# Standalone verification for Alibaba model fix. Run manually from repo root.
# Delegates to scripts/tests/test_alibaba_fix.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/tests/test_alibaba_fix.sh"
