#!/usr/bin/env bash
# Test the binary tarball installer on a given distro image.
# Usage: test-tarball.sh <tarball> <image> [label]
set -euo pipefail

TARBALL="${1:-}"
IMAGE="${2:-}"
LABEL="${3:-$IMAGE}"

[[ -f "$TARBALL" ]] || { echo "✗ Tarball not found: $TARBALL"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "⚠ docker not found — skipping"; exit 2; }

TARBALL_NAME="$(basename "$TARBALL")"
echo "→ Testing $TARBALL_NAME installer on $LABEL"

INNER="$(mktemp)"
cat > "$INNER" << 'INNEREOF'
#!/usr/bin/env bash
set -euo pipefail

if command -v dnf &>/dev/null; then
    dnf install -y python3-pip python3-PyQt6 python3-pyyaml 2>/dev/null | tail -3
elif command -v zypper &>/dev/null; then
    zypper install -y python3-pip python3-qt6 python3-yaml 2>/dev/null | tail -3
elif command -v apt-get &>/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y python3-pip python3-pyqt6 python3-yaml 2>/dev/null | tail -3
elif command -v pacman &>/dev/null; then
    pacman -Sy --noconfirm python-pip python-pyqt6 python-yaml 2>/dev/null | tail -3
fi

mkdir -p /tmp/yabridge-test
tar -xzf /tmp/yabridge.tar.gz -C /tmp/yabridge-test --strip-components=1

cd /tmp/yabridge-test
bash install --non-interactive

echo "→ Verifying installation"
python3 -c "import yabridge_gui; print('yabridge_gui import OK')"
test -f "$HOME/.local/share/applications/yabridge-gui-controller.desktop" && echo "desktop file OK"
test -f "$HOME/.local/share/icons/hicolor/256x256/apps/yabridge-gui-controller.png" && echo "icon OK"
echo "All checks passed"
INNEREOF

docker run --rm \
    -v "$TARBALL:/tmp/yabridge.tar.gz:ro,z" \
    -v "$INNER:/build-inner.sh:ro,z" \
    "$IMAGE" \
    bash /build-inner.sh

rm -f "$INNER"
echo "✓ $TARBALL_NAME on $LABEL — OK"
