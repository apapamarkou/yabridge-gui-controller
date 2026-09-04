#!/usr/bin/env bash
# Build a binary tarball: yabridge-gui-controller-VERSION-linux.tar.gz
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(grep '^fallback_version' "$REPO_ROOT/pyproject.toml" | sed 's/.*= *"\(.*\)"/\1/')"
OUTPUT="$REPO_ROOT/packaging/output"
NAME="yabridge-gui-controller-$VERSION-linux"
STAGING="$OUTPUT/$NAME"

mkdir -p "$OUTPUT"
rm -rf "$STAGING"
mkdir -p "$STAGING"

echo "→ Building wheel"
python3 -m pip wheel "$REPO_ROOT" --no-deps -w "$STAGING/wheels" -q

echo "→ Copying assets"
cp "$REPO_ROOT/packaging/specs/yabridge-gui-controller.desktop" "$STAGING/"
cp "$REPO_ROOT/src/yabridge-gui-controller.png"                 "$STAGING/"
cp "$REPO_ROOT/README.md"                                       "$STAGING/"
cp "$REPO_ROOT/install"                                         "$STAGING/install"
chmod +x "$STAGING/install"

echo "→ Creating tarball"
tar -czf "$OUTPUT/$NAME.tar.gz" -C "$OUTPUT" "$NAME"
rm -rf "$STAGING"

echo "✓ $OUTPUT/$NAME.tar.gz"
