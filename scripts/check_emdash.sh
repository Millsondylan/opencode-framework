#!/usr/bin/env bash
# check_emdash.sh
# Scan tracked files for banned horizontal dashes at codepoints
# 8210 (U+2012), 8211 (U+2013), 8212 (U+2014), 8213 (U+2015).
# Exit 0 if clean, 1 if any match. --fix replaces with ASCII hyphen.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

FIX=0
ROOT_DIR="."
for arg in "$@"; do
    case "${arg}" in
        --fix) FIX=1 ;;
        --help|-h)
            echo "Usage: check_emdash.sh [--fix] [root_dir]"
            exit 0
            ;;
        *) ROOT_DIR="${arg}" ;;
    esac
done

cd "${ROOT_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}[FAIL]${NC} python3 required"
    exit 1
fi

# Decimal codepoints passed via env. Python builds the regex via chr().
export DASH_CODEPOINTS="8210,8211,8212,8213"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    FILE_LIST=$(git ls-files)
else
    FILE_LIST=$(find . -type f -not -path '*/\.git/*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*')
fi

TOTAL_FILES=0
SCAN_OUTPUT=$(mktemp)
trap 'rm -f "${SCAN_OUTPUT}"' EXIT

while IFS= read -r f; do
    [ -z "${f}" ] && continue
    [ ! -f "${f}" ] && continue
    if file "${f}" 2>/dev/null | grep -qiE 'binary|image|archive|compressed'; then
        continue
    fi
    TOTAL_FILES=$((TOTAL_FILES + 1))

    python3 -c '
import sys, re, os
path = sys.argv[1]
cps = [int(x) for x in os.environ["DASH_CODEPOINTS"].split(",")]
charset = "".join(chr(c) for c in cps)
pat = re.compile("[" + re.escape(charset) + "]")
try:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, start=1):
            for m in pat.finditer(line):
                print("%s:%d:%d:U+%04X" % (path, lineno, m.start(), ord(m.group())))
except Exception as e:
    print("%s:0:0:READ_ERROR:%s" % (path, e))
' "${f}" >> "${SCAN_OUTPUT}" || true
done <<< "${FILE_LIST}"

if [ -s "${SCAN_OUTPUT}" ]; then
    VIOLATION_COUNT=$(wc -l < "${SCAN_OUTPUT}" | tr -d ' ')
    VIOLATION_FILES=$(awk -F: '{print $1}' "${SCAN_OUTPUT}" | sort -u | wc -l | tr -d ' ')
    echo -e "${RED}Banned dash violations:${NC}"
    cat "${SCAN_OUTPUT}"
    echo ""
    echo -e "${RED}[FAIL]${NC} ${VIOLATION_COUNT} violations in ${VIOLATION_FILES} files (scanned ${TOTAL_FILES})"

    if [ "${FIX}" -eq 1 ]; then
        echo -e "${YELLOW}Applying fix: replacing banned dashes with ASCII hyphen${NC}"
        awk -F: '{print $1}' "${SCAN_OUTPUT}" | sort -u | while IFS= read -r target; do
            python3 -c '
import sys, re, os
path = sys.argv[1]
cps = [int(x) for x in os.environ["DASH_CODEPOINTS"].split(",")]
charset = "".join(chr(c) for c in cps)
pat = re.compile("[" + re.escape(charset) + "]")
with open(path, "r", encoding="utf-8", errors="replace") as fh:
    text = fh.read()
new = pat.sub("-", text)
if new != text:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("fixed: " + path)
' "${target}"
        done
        echo -e "${YELLOW}Rescanning after fix${NC}"
        exec "$0" "${ROOT_DIR}"
    fi
    exit 1
fi

echo -e "${GREEN}[PASS]${NC} Zero banned dashes across ${TOTAL_FILES} files"
exit 0
