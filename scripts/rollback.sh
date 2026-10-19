#!/usr/bin/env bash
# rollback.sh
# Revert a Google Play track to the previous version_code.
# Usage: rollback.sh --track <track> [--version <code>] [--app <package>]
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

LOG_DIR="${HOME}/.opencode/logs"
LOG_FILE="${LOG_DIR}/rollback.log"
mkdir -p "${LOG_DIR}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG_FILE}"; }
pass() { echo -e "${GREEN}[PASS]${NC} $1" | tee -a "${LOG_FILE}"; }
fail() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "${LOG_FILE}"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${LOG_FILE}"; }
die() { fail "$1"; exit 1; }

TRACK=""
VERSION=""
APP_ID=""

while [ $# -gt 0 ]; do
    case "$1" in
        --track) TRACK="$2"; shift 2 ;;
        --version) VERSION="$2"; shift 2 ;;
        --app) APP_ID="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: rollback.sh --track <track> [--version <code>] [--app <package>]"
            echo "  If --version omitted, rolls back to immediately prior version on track."
            exit 0
            ;;
        *) die "Unknown argument: $1" ;;
    esac
done

case "${TRACK}" in
    internal|alpha|beta|production) ;;
    *) die "--track must be one of internal, alpha, beta, production" ;;
esac

log "==== Rollback Start: track=${TRACK} ===="

PLAY_SCRIPT="publishing/play/release.py"
if [ ! -f "${PLAY_SCRIPT}" ]; then
    die "publishing/play/release.py not found; cannot rollback"
fi
if ! command -v python3 >/dev/null 2>&1; then
    die "python3 required"
fi

# Step 1: halt current rollout
log "Step 1: halt current rollout on ${TRACK}"
HALT_ARGS=(--track "${TRACK}" --halt)
[ -n "${APP_ID}" ] && HALT_ARGS+=(--package-name "${APP_ID}")
if python3 "${PLAY_SCRIPT}" "${HALT_ARGS[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
    pass "rollout halted on ${TRACK}"
else
    warn "halt returned non-zero (track may already be halted)"
fi

# Step 2: determine target version
if [ -z "${VERSION}" ]; then
    log "Step 2: discovering prior version on ${TRACK}"
    PRIOR_ARGS=(--track "${TRACK}" --list-prior)
    [ -n "${APP_ID}" ] && PRIOR_ARGS+=(--package-name "${APP_ID}")
    VERSION=$(python3 "${PLAY_SCRIPT}" "${PRIOR_ARGS[@]}" 2>>"${LOG_FILE}" | tail -n1 | tr -d '[:space:]' || true)
    if [ -z "${VERSION}" ]; then
        die "Could not resolve prior version on ${TRACK}. Pass --version explicitly."
    fi
    pass "prior version resolved: ${VERSION}"
else
    log "Using supplied rollback version: ${VERSION}"
fi

# Step 3: promote prior version back to track
log "Step 3: promote version ${VERSION} back to ${TRACK}"
PROMOTE_ARGS=(--track "${TRACK}" --rollback-to "${VERSION}")
[ -n "${APP_ID}" ] && PROMOTE_ARGS+=(--package-name "${APP_ID}")
if python3 "${PLAY_SCRIPT}" "${PROMOTE_ARGS[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
    pass "rollback promotion ok"
else
    die "rollback promotion failed"
fi

# Step 4: record rollback in decision record
DECISION_DIR="docs/decisions"
if [ -d "${DECISION_DIR}" ]; then
    TS=$(date -u +%Y-%m-%d)
    RECORD="${DECISION_DIR}/${TS}-rollback-${TRACK}-${VERSION}.md"
    cat > "${RECORD}" <<EOF
# Rollback: ${TRACK} to version ${VERSION}

Date: ${TS}
Track: ${TRACK}
Reverted to version_code: ${VERSION}
Operator: $(whoami)
Command: rollback.sh --track ${TRACK} --version ${VERSION}

## Reason
Populate before merge. Attach incident link if applicable.

## Next Steps
1. Confirm crash rate drops on Play console.
2. File follow-up work to land fix before re-release.
EOF
    pass "decision record written: ${RECORD}"
fi

log "==== Rollback End: ${TRACK} at ${VERSION} ===="
echo -e "${GREEN}Rollback complete.${NC}"
exit 0
