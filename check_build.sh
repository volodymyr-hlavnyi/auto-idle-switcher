#!/usr/bin/env bash
set -euo pipefail

SCRIPT=make_build.sh
PKG_NAME=auto-idle

# 1) Basic checks
if [ ! -f "$SCRIPT" ]; then
  echo "ERROR: expected script $SCRIPT not found" >&2
  exit 1
fi

# Find the latest source deb tree for the package (sorted by version)
SRC_DEB=$(ls -d deb/${PKG_NAME}_* 2>/dev/null | sort -V | tail -n 1 || true)
if [ -z "$SRC_DEB" ]; then
  echo "ERROR: no deb/${PKG_NAME}_* folder found" >&2
  exit 1
fi

# Ensure the .deb file exists
DEB_FILE="${SRC_DEB}"
if [[ ! "$DEB_FILE" == *.deb ]]; then
  DEB_FILE="${SRC_DEB}.deb"
fi

if [ ! -f "$DEB_FILE" ]; then
  echo "ERROR: $DEB_FILE not found" >&2
  exit 1
fi

# Extract the .deb file to a temporary directory
TEST_DIR=$(mktemp -d /tmp/${PKG_NAME}_test_pkg.XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT
dpkg-deb -x "$DEB_FILE" "$TEST_DIR"
dpkg-deb -e "$DEB_FILE" "$TEST_DIR/DEBIAN"



# Locate the DEBIAN/control file
CONTROL_FILE=$(find "$TEST_DIR" -type f -path "*/DEBIAN/control" | head -n 1)
if [ -z "$CONTROL_FILE" ]; then
  echo "ERROR: DEBIAN/control file not found in extracted package" >&2
  exit 1
fi

# Ensure usr/bin/auto-idle exists in the extracted directory
if [ ! -f "$TEST_DIR/usr/bin/auto-idle" ]; then
  echo "ERROR: $TEST_DIR/usr/bin/auto-idle not found" >&2
  exit 1
fi

# 2) Syntax check
bash -n "$SCRIPT"

# 3) Lint if available
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "$SCRIPT" || true
else
  echo "note: shellcheck not installed, skipping lint"
fi

# 4) Inspect results in the test folder
echo
echo "control file:"
sed -n '1,120p' "$CONTROL_FILE" || true
echo
echo "launcher (first 40 lines):"
sed -n '1,40p' "$TEST_DIR/usr/bin/auto-idle" || true
echo
echo "permissions:"
find "$TEST_DIR" -ls

# 5) Instructions for final build left unchanged
echo
echo "Dry-run complete. To produce a real .deb use the original $SCRIPT."