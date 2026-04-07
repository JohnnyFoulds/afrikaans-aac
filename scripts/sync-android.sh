#!/usr/bin/env bash
# sync-android.sh — rsync literature/mp3/ to Android phone and trigger MediaStore rescan
#
# Usage: bash scripts/sync-android.sh
# Run from repo root: ~/code/unisa/unisa-phd-proposal/

set -euo pipefail

ANDROID_USER="u0_a356"
ANDROID_HOST="192.168.1.101"
ANDROID_PORT="8022"
ANDROID_DEST="~/storage/music/unisa/"
LOCAL_SRC="literature/mp3/"

SSH_OPTS="-p ${ANDROID_PORT} -o StrictHostKeyChecking=no -o PasswordAuthentication=no"

echo "=== Syncing ${LOCAL_SRC} → ${ANDROID_HOST}:${ANDROID_DEST} ==="
rsync -avz --progress -e "ssh ${SSH_OPTS}" \
    "${LOCAL_SRC}" "${ANDROID_USER}@${ANDROID_HOST}:${ANDROID_DEST}"

echo ""
echo "=== Triggering Android MediaStore rescan ==="
ssh ${SSH_OPTS} "${ANDROID_USER}@${ANDROID_HOST}" \
    'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///storage/emulated/0/Music/unisa/ 2>&1 && am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///storage/emulated/0 2>&1'

echo ""
echo "Done. Files should appear in Samsung Music."
