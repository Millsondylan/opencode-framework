#!/usr/bin/env bash
# backup-dump.sh
# Daily logical Supabase dump, age-encrypted, uploaded to Cloudflare R2.
# Retention: 14 days. Invoke from launchd plist com.opencode.backup-watcher.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

LOG_DIR="${HOME}/.opencode/logs"
LOG_FILE="${LOG_DIR}/backup-dump.log"
mkdir -p "${LOG_DIR}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG_FILE}"; }
pass() { echo -e "${GREEN}[PASS]${NC} $1" | tee -a "${LOG_FILE}"; }
fail() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "${LOG_FILE}"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${LOG_FILE}"; }

: "${SUPABASE_PROJECT_REF:=}"
: "${R2_BUCKET:=opencode-backups}"
: "${R2_ENDPOINT:=}"
: "${AGE_RECIPIENTS_FILE:=${HOME}/WORK/Agents.2/opencode-framework/docs/keys/backup-recipients.txt}"
: "${RETENTION_DAYS:=14}"

log "==== Backup Dump Start ===="

# Dependency checks
for bin in supabase age aws gzip; do
    if ! command -v "${bin}" >/dev/null 2>&1; then
        fail "required binary missing: ${bin}"
        exit 1
    fi
done
pass "dependencies present"

if [ ! -f "${AGE_RECIPIENTS_FILE}" ]; then
    fail "age recipients file not found: ${AGE_RECIPIENTS_FILE}"
    exit 1
fi
pass "age recipients file found"

# Dump
TS=$(date -u +%Y%m%dT%H%M%SZ)
WORK_DIR=$(mktemp -d)
DUMP_PLAIN="${WORK_DIR}/supabase-${TS}.sql.gz"
DUMP_ENC="${WORK_DIR}/supabase-${TS}.sql.gz.age"

log "Dumping Supabase project ref=${SUPABASE_PROJECT_REF}"
if [ -n "${SUPABASE_PROJECT_REF}" ]; then
    supabase db dump --project-ref "${SUPABASE_PROJECT_REF}" 2>>"${LOG_FILE}" | gzip > "${DUMP_PLAIN}" \
        && pass "dump written to ${DUMP_PLAIN}" \
        || { fail "dump failed"; rm -rf "${WORK_DIR}"; exit 1; }
else
    warn "SUPABASE_PROJECT_REF unset; creating placeholder dump"
    echo "-- placeholder dump ${TS}" | gzip > "${DUMP_PLAIN}"
fi

# Encrypt
log "Encrypting dump with age"
AGE_RECIPIENT=$(grep -v '^#' "${AGE_RECIPIENTS_FILE}" | head -n1 || true)
if [ -z "${AGE_RECIPIENT}" ]; then
    fail "no age recipient parsed from ${AGE_RECIPIENTS_FILE}"
    rm -rf "${WORK_DIR}"
    exit 1
fi

age --recipient "${AGE_RECIPIENT}" --output "${DUMP_ENC}" "${DUMP_PLAIN}" \
    && pass "encrypted to ${DUMP_ENC}" \
    || { fail "encryption failed"; rm -rf "${WORK_DIR}"; exit 1; }

# Shred plaintext
if command -v shred >/dev/null 2>&1; then
    shred -u "${DUMP_PLAIN}" 2>/dev/null || rm -f "${DUMP_PLAIN}"
else
    rm -P "${DUMP_PLAIN}" 2>/dev/null || rm -f "${DUMP_PLAIN}"
fi
pass "plaintext dump shredded"

# Upload to R2
REMOTE_KEY="daily/${TS}.sql.gz.age"
log "Uploading to s3://${R2_BUCKET}/${REMOTE_KEY}"
if [ -n "${R2_ENDPOINT}" ]; then
    aws s3 cp "${DUMP_ENC}" "s3://${R2_BUCKET}/${REMOTE_KEY}" \
        --endpoint-url "${R2_ENDPOINT}" \
        >>"${LOG_FILE}" 2>&1 \
        && pass "upload ok" \
        || { fail "upload failed"; rm -rf "${WORK_DIR}"; exit 1; }
else
    warn "R2_ENDPOINT unset; skipping upload"
fi

rm -rf "${WORK_DIR}"

# Retention rotation: delete objects older than RETENTION_DAYS
log "Retention rotation: ${RETENTION_DAYS} days"
if [ -n "${R2_ENDPOINT}" ]; then
    CUTOFF=$(date -u -v-"${RETENTION_DAYS}"d +%Y-%m-%d 2>/dev/null || date -u -d "${RETENTION_DAYS} days ago" +%Y-%m-%d)
    log "Cutoff date: ${CUTOFF}"
    aws s3 ls "s3://${R2_BUCKET}/daily/" --endpoint-url "${R2_ENDPOINT}" 2>/dev/null | \
        while read -r line; do
            d=$(echo "${line}" | awk '{print $1}')
            f=$(echo "${line}" | awk '{print $4}')
            if [ -n "${d}" ] && [ -n "${f}" ] && [ "${d}" \< "${CUTOFF}" ]; then
                log "Deleting old backup: ${f}"
                aws s3 rm "s3://${R2_BUCKET}/daily/${f}" --endpoint-url "${R2_ENDPOINT}" >>"${LOG_FILE}" 2>&1 || true
            fi
        done
    pass "retention rotation complete"
else
    warn "R2_ENDPOINT unset; skipping retention"
fi

log "==== Backup Dump End ===="
exit 0
