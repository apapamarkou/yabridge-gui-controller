#!/usr/bin/env bash
# Test .tar.gz portable package across all supported distros
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARBALL=$(ls "$ROOT"/dist/*.tar.gz 2>/dev/null | grep -v "\.whl" | head -1)

if [ -z "$TARBALL" ]; then
    echo "No .tar.gz found in dist/. Run 'make package' first."
    exit 1
fi

TARBALL_FILE="$(basename "$TARBALL")"

echo "Testing tarball: $TARBALL_FILE"

declare -A IMAGES=(
    ["debian:13"]="apt-get install -y python3-pyqt6 python3-yaml"
    ["ubuntu:24.04"]="apt-get install -y python3-pyqt6 python3-yaml"
    ["fedora:44"]="dnf install -y python3-PyQt6 python3-pyyaml"
    ["archlinux:latest"]="pacman -Sy --noconfirm python-pyqt6 python-yaml"
)

for IMAGE in "${!IMAGES[@]}"; do
    INSTALL_CMD="${IMAGES[$IMAGE]}"
    echo ""
    echo "=== Testing on $IMAGE ==="
    docker run --rm \
        -v "$TARBALL:/tmp/$TARBALL_FILE:ro" \
        "$IMAGE" \
        bash -c "
            $INSTALL_CMD &&
            cd /tmp &&
            tar -xzf $TARBALL_FILE &&
            cd \$(ls -d */ | head -1) &&
            python3 -c 'import sys; sys.path.insert(0,\".\"); from yabridge_gui import __version__; print(\"Version:\", __version__)' &&
            echo 'PASS: $IMAGE'
        " && echo "✓ $IMAGE" || echo "✗ $IMAGE FAILED"
done
