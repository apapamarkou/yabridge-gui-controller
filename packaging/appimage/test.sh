#!/usr/bin/env bash
# Test AppImage
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APPIMAGE=$(ls "$ROOT"/dist/*.AppImage 2>/dev/null | head -1)

if [ -z "$APPIMAGE" ]; then
    echo "No .AppImage found in dist/. Run 'make package' first."
    exit 1
fi

echo "Testing AppImage: $(basename "$APPIMAGE")"
chmod +x "$APPIMAGE"

# Basic import test via AppImage's embedded Python
"$APPIMAGE" --appimage-extract-and-run python3 -c \
    "from yabridge_gui import __version__; print('Version:', __version__)" \
    && echo "✓ AppImage import test passed" \
    || echo "✗ AppImage import test FAILED"
