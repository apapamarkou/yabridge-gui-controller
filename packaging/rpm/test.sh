#!/usr/bin/env bash
# Test .rpm package installation in a Fedora container
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RPM=$(ls "$ROOT"/dist/*.rpm 2>/dev/null | head -1)

if [ -z "$RPM" ]; then
    echo "No .rpm found in dist/. Run 'make package' first."
    exit 1
fi

RPM_FILE="$(basename "$RPM")"

echo "Testing .rpm: $RPM_FILE"
echo ""
echo "=== Testing on fedora:44 ==="
docker run --rm \
    -v "$RPM:/tmp/$RPM_FILE:ro" \
    fedora:44 \
    bash -c "
        dnf install -y python3-PyQt6 python3-pyyaml &&
        rpm -i /tmp/$RPM_FILE &&
        python3 -c 'from yabridge_gui import __version__; print(\"Version:\", __version__)' &&
        echo 'PASS: fedora:44'
    " && echo "✓ fedora:44" || echo "✗ fedora:44 FAILED"
