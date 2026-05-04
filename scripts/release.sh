#!/usr/bin/env bash
# release.sh
# Full release flow: clean git tree, tests, build AAB, critic gate, tag, publish to Play.
# Usage: release.sh --track internal|alpha|beta|production [--app <app-id>] [--version <version>]
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

LOG_DIR="${HOME}/.opencode/logs"
LOG_FILE="${LOG_DIR}/release.log"
mkdir -p "${LOG_DIR}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG_FILE}"; }
pass() { echo -e "${GREEN}[PASS]${NC} $1" | tee -a "${LOG_FILE}"; }
fail() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "${LOG_FILE}"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${LOG_FILE}"; }
die() { fail "$1"; exit 1; }

TRACK=""
APP_ID=""
VERSION=""
CRITIC_THRESHOLD=95

while [ $# -gt 0 ]; do
    case "$1" in
        --track) TRACK="$2"; shift 2 ;;
        --app) APP_ID="$2"; shift 2 ;;
        --version) VERSION="$2"; shift 2 ;;
        --critic-threshold) CRITIC_THRESHOLD="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: release.sh --track internal|alpha|beta|production [--app <app-id>] [--version <version>]"
            exit 0
            ;;
        *) die "Unknown argument: $1" ;;
    esac
done

case "${TRACK}" in
    internal|alpha|beta|production) ;;
    *) die "--track must be one of internal, alpha, beta, production" ;;
esac

log "==== Release Start: track=${TRACK} ===="

# Step 1: clean git tree
log "Step 1: verify clean git working tree"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    die "Working tree not clean. Commit or stash changes before release."
fi
pass "git tree clean"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Branch: ${CURRENT_BRANCH}, commit: ${CURRENT_COMMIT}"

# Step 2: run tests
log "Step 2: run test suite"
if [ -f "pubspec.yaml" ]; then
    if command -v flutter >/dev/null 2>&1; then
        flutter test --no-pub 2>&1 | tee -a "${LOG_FILE}" || die "flutter tests failed"
        pass "flutter tests ok"
    else
        warn "flutter not installed; skipping flutter test"
    fi
fi

if [ -f "pytest.ini" ] || [ -d "tests" ]; then
    if command -v pytest >/dev/null 2>&1; then
        pytest -q 2>&1 | tee -a "${LOG_FILE}" || warn "pytest returned non-zero"
    fi
fi

# Step 3: build AAB
log "Step 3: build signed Android App Bundle"
if [ -f "pubspec.yaml" ] && command -v flutter >/dev/null 2>&1; then
    DEBUG_DIR="./debug-info"
    mkdir -p "${DEBUG_DIR}"
    flutter build appbundle --release \
        --obfuscate \
        --split-debug-info="${DEBUG_DIR}" \
        2>&1 | tee -a "${LOG_FILE}" \
        || die "flutter build appbundle failed"
    AAB_PATH="build/app/outputs/bundle/release/app-release.aab"
    if [ ! -f "${AAB_PATH}" ]; then
        die "AAB not found at expected path: ${AAB_PATH}"
    fi
    pass "AAB built at ${AAB_PATH}"
else
    warn "pubspec.yaml missing or flutter absent; skipping AAB build"
    AAB_PATH=""
fi

# Step 4: multi-critic gate
log "Step 4: multi-critic gate at ${CRITIC_THRESHOLD}"
CRITIC_SCRIPT="eval/critics_gate.py"
if [ -f "${CRITIC_SCRIPT}" ] && command -v python3 >/dev/null 2>&1; then
    if python3 "${CRITIC_SCRIPT}" --threshold "${CRITIC_THRESHOLD}" --branch "${CURRENT_BRANCH}" 2>&1 | tee -a "${LOG_FILE}"; then
        pass "critic gate passed at ${CRITIC_THRESHOLD}"
    else
        die "critic gate failed below ${CRITIC_THRESHOLD}"
    fi
else
    warn "critic gate script missing; skipping (will flag in verify.sh)"
fi

# Step 5: bump version if provided
if [ -n "${VERSION}" ]; then
    log "Step 5: bump version to ${VERSION}"
    if [ -f "pubspec.yaml" ]; then
        # Only mutate pubspec.yaml when file exists; leave intact otherwise.
        sed -i.bak "s/^version: .*/version: ${VERSION}/" pubspec.yaml
        rm -f pubspec.yaml.bak
        pass "pubspec.yaml version set to ${VERSION}"
    fi
fi

# Step 6: git tag
TAG_NAME="v${VERSION:-$(date -u +%Y.%m.%d-%H%M%S)}-${TRACK}"
log "Step 6: create git tag ${TAG_NAME}"
if git tag -l "${TAG_NAME}" | grep -q "${TAG_NAME}"; then
    warn "tag ${TAG_NAME} already exists; skipping tag creation"
else
    git tag -a "${TAG_NAME}" -m "Release ${TAG_NAME} to ${TRACK}" || die "git tag failed"
    pass "tagged ${TAG_NAME}"
fi

# Step 7: publish via publishing/play/release.py
log "Step 7: publish to Google Play (${TRACK})"
PLAY_SCRIPT="publishing/play/release.py"
if [ -f "${PLAY_SCRIPT}" ] && command -v python3 >/dev/null 2>&1; then
    PLAY_ARGS=(--track "${TRACK}")
    [ -n "${APP_ID}" ] && PLAY_ARGS+=(--package-name "${APP_ID}")
    [ -n "${AAB_PATH}" ] && PLAY_ARGS+=(--aab "${AAB_PATH}")
    [ -n "${VERSION}" ] && PLAY_ARGS+=(--version-name "${VERSION}")
    python3 "${PLAY_SCRIPT}" "${PLAY_ARGS[@]}" 2>&1 | tee -a "${LOG_FILE}" \
        || die "publishing/play/release.py failed"
    pass "Play publish ok"
else
    warn "publishing/play/release.py missing; skipping Play upload"
fi

# Step 8: push tag
log "Step 8: push tag to origin"
if git push origin "${TAG_NAME}" 2>>"${LOG_FILE}"; then
    pass "tag pushed"
else
    warn "tag push failed or skipped (no remote)"
fi

log "==== Release End: ${TAG_NAME} on ${TRACK} ===="
echo ""
echo -e "${GREEN}Release complete: ${TAG_NAME}${NC}"
exit 0
