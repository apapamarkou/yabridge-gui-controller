#!/usr/bin/env bash
# Build a source tarball: yabridge-gui-controller-VERSION.tar.gz
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(grep '^fallback_version' "$REPO_ROOT/pyproject.toml" | sed 's/.*= *"\(.*\)"/\1/')"
OUTPUT="$REPO_ROOT/packaging/output"
NAME="yabridge-gui-controller-$VERSION"

mkdir -p "$OUTPUT"

echo "→ Building source tarball $NAME.tar.gz"
git -C "$REPO_ROOT" archive --format=tar.gz --prefix="$NAME/" HEAD \
    -o "$OUTPUT/$NAME.tar.gz"

echo "✓ $OUTPUT/$NAME.tar.gz"
