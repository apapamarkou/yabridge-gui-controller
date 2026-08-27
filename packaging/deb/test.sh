#!/usr/bin/env bash
# Test .deb package installation in a Debian/Ubuntu container
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEB=$(ls "$ROOT"/dist/*.deb 2>/dev/null | head -1)

if [ -z "$DEB" ]; then
    echo "No .deb found in dist/. Run 'make package' first."
    exit 1
fi

DEB_FILE="$(basename "$DEB")"

echo "Testing .deb: $DEB_FILE"

for IMAGE in debian:13 ubuntu:26.04; do
    echo ""
    echo "=== Testing on $IMAGE ==="
    docker run --rm \
        -v "$DEB:/tmp/$DEB_FILE:ro" \
        "$IMAGE" \
        bash -c "
            apt-get update -q &&
            apt-get install -y python3-pyqt6 python3-yaml &&
            dpkg -i /tmp/$DEB_FILE &&
            python3 -c 'from yabridge_gui import __version__; print(\"Version:\", __version__)' &&
            echo 'PASS: $IMAGE'
        " && echo "✓ $IMAGE" || echo "✗ $IMAGE FAILED"
done
