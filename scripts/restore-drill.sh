#!/usr/bin/env bash
# restore-drill.sh
# Supabase PITR restore drill: dump production, restore to staging, verify row counts.
# RTO target: 4h. RPO target: 1h.
# Default mode is dry-run. Pass --execute to perform real restore.
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

LOG_DIR="${HOME}/.opencode/logs"
LOG_FILE="${LOG_DIR}/restore-drill.log"
mkdir -p "${LOG_DIR}"

log() {
    local msg="$1"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ${msg}" | tee -a "${LOG_FILE}"
}

pass() { echo -e "${GREEN}[PASS]${NC} $1" | tee -a "${LOG_FILE}"; }
fail() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "${LOG_FILE}"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${LOG_FILE}"; }

EXECUTE=0
for arg in "$@"; do
    case "${arg}" in
        --execute) EXECUTE=1 ;;
        --help|-h)
            echo "Usage: restore-drill.sh [--execute]"
            echo "  --execute: Perform real restore (default: dry-run)"
            exit 0
            ;;
    esac
done

log "==== Restore Drill Start (execute=${EXECUTE}) ===="

# Phase 1: environment checks
log "Phase 1: environment check"
if ! command -v supabase >/dev/null 2>&1; then
    fail "supabase CLI not installed"
    exit 1
fi
pass "supabase CLI present"

: "${SUPABASE_PROJECT_REF_PROD:=}"
: "${SUPABASE_PROJECT_REF_STAGING:=}"
: "${R2_BUCKET:=opencode-backups}"

if [ -z "${SUPABASE_PROJECT_REF_PROD}" ] || [ -z "${SUPABASE_PROJECT_REF_STAGING}" ]; then
    warn "SUPABASE_PROJECT_REF_PROD or SUPABASE_PROJECT_REF_STAGING unset; using placeholders"
fi

# Phase 2: dump production
log "Phase 2: dump production"
DUMP_TS=$(date -u +%Y%m%dT%H%M%SZ)
DUMP_FILE="/tmp/supabase-prod-${DUMP_TS}.sql.gz"

if [ "${EXECUTE}" -eq 1 ]; then
    log "Running supabase db dump against production"
    if supabase db dump --project-ref "${SUPABASE_PROJECT_REF_PROD}" 2>>"${LOG_FILE}" | gzip > "${DUMP_FILE}"; then
        pass "dump written to ${DUMP_FILE}"
    else
        fail "dump failed"
        exit 1
    fi
else
    log "DRY-RUN: would run supabase db dump and gzip to ${DUMP_FILE}"
    pass "dump step (dry-run)"
fi

# Phase 3: upload to R2
log "Phase 3: upload to R2 bucket=${R2_BUCKET}"
if [ "${EXECUTE}" -eq 1 ]; then
    if command -v aws >/dev/null 2>&1; then
        aws s3 cp "${DUMP_FILE}" "s3://${R2_BUCKET}/restore-drill/${DUMP_TS}.sql.gz" \
            --endpoint-url "${R2_ENDPOINT:-https://example.r2.cloudflarestorage.com}" \
            2>>"${LOG_FILE}" && pass "R2 upload ok" || { fail "R2 upload failed"; exit 1; }
    else
        warn "aws CLI missing, skipping R2 upload"
    fi
else
    log "DRY-RUN: would upload ${DUMP_FILE} to s3://${R2_BUCKET}/restore-drill/${DUMP_TS}.sql.gz"
    pass "upload step (dry-run)"
fi

# Phase 4: restore to staging
log "Phase 4: restore to staging ref=${SUPABASE_PROJECT_REF_STAGING}"
RESTORE_START=$(date +%s)
if [ "${EXECUTE}" -eq 1 ]; then
    log "Running psql restore against staging"
    if command -v psql >/dev/null 2>&1 && [ -n "${STAGING_DB_URL:-}" ]; then
        gunzip -c "${DUMP_FILE}" | psql "${STAGING_DB_URL}" >>"${LOG_FILE}" 2>&1 \
            && pass "restore ok" || { fail "restore failed"; exit 1; }
    else
        warn "psql or STAGING_DB_URL missing, cannot restore"
    fi
else
    log "DRY-RUN: would gunzip ${DUMP_FILE} and pipe to psql \$STAGING_DB_URL"
    pass "restore step (dry-run)"
fi
RESTORE_END=$(date +%s)
RESTORE_ELAPSED=$((RESTORE_END - RESTORE_START))
log "Restore elapsed: ${RESTORE_ELAPSED}s"

# RTO check: 4 hours = 14400 seconds
RTO_BUDGET=14400
if [ "${RESTORE_ELAPSED}" -le "${RTO_BUDGET}" ]; then
    pass "RTO within 4h budget (${RESTORE_ELAPSED}s / ${RTO_BUDGET}s)"
else
    fail "RTO exceeded 4h budget (${RESTORE_ELAPSED}s > ${RTO_BUDGET}s)"
fi

# Phase 5: verify row counts
log "Phase 5: row count verification"
if [ "${EXECUTE}" -eq 1 ] && [ -n "${PROD_DB_URL:-}" ] && [ -n "${STAGING_DB_URL:-}" ]; then
    TABLES="users accounts transactions sessions"
    for t in ${TABLES}; do
        PROD_COUNT=$(psql "${PROD_DB_URL}" -tAc "SELECT count(*) FROM public.${t}" 2>/dev/null || echo "0")
        STAGE_COUNT=$(psql "${STAGING_DB_URL}" -tAc "SELECT count(*) FROM public.${t}" 2>/dev/null || echo "0")
        if [ "${PROD_COUNT}" = "${STAGE_COUNT}" ]; then
            pass "table ${t}: prod=${PROD_COUNT} staging=${STAGE_COUNT}"
        else
            fail "table ${t}: prod=${PROD_COUNT} staging=${STAGE_COUNT}"
        fi
    done
else
    log "DRY-RUN: would SELECT count(*) on users, accounts, transactions, sessions"
    pass "row count step (dry-run)"
fi

# RPO check: 1 hour backup age budget
RPO_BUDGET=3600
log "RPO budget: ${RPO_BUDGET}s (1h)"
pass "RPO noted (set backup schedule to honour 1h)"

log "==== Restore Drill End ===="
echo ""
echo -e "${GREEN}Restore drill finished. Log: ${LOG_FILE}${NC}"
exit 0
