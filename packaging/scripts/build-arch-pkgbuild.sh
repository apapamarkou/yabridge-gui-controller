#!/usr/bin/env bash
# Generate a PKGBUILD for Arch Linux and test it with makepkg in Docker.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(grep '^fallback_version' "$REPO_ROOT/pyproject.toml" | sed 's/.*= *"\(.*\)"/\1/')"
OUTPUT="$REPO_ROOT/packaging/output"
PKGBUILD_DIR="$OUTPUT/arch"

mkdir -p "$PKGBUILD_DIR"

LOCAL_TARBALL="$PKGBUILD_DIR/yabridge-gui-controller-$VERSION.tar.gz"
git -C "$REPO_ROOT" archive --format=tar.gz --prefix="yabridge-gui-controller-$VERSION/" HEAD \
    -o "$LOCAL_TARBALL"
SHA256="$(sha256sum "$LOCAL_TARBALL" | cut -d' ' -f1)"

echo "→ Generating PKGBUILD for yabridge-gui-controller $VERSION"
cat > "$PKGBUILD_DIR/PKGBUILD" << EOF
# Maintainer: Andrianos Papamarkou <andrianos@example.com>
pkgname=yabridge-gui-controller
pkgver=$VERSION
pkgrel=1
pkgdesc="GUI controller for yabridge — manage Windows VST/VST3 plugins on Linux"
arch=('any')
url="https://github.com/apapamarkou/yabridge-gui-controller"
license=('GPL-3.0-or-later')
depends=('python>=3.10' 'python-pyqt6' 'python-yaml')
makedepends=('python-pip' 'python-setuptools')
source=("https://github.com/apapamarkou/yabridge-gui-controller/archive/refs/tags/v\${pkgver}.tar.gz")
sha256sums=('$SHA256')

build() {
    cd "\$srcdir/yabridge-gui-controller-\$pkgver"
    python -m pip wheel --no-build-isolation --no-deps -w dist .
}

package() {
    cd "\$srcdir/yabridge-gui-controller-\$pkgver"
    python -m pip install --no-deps --root="\$pkgdir" --prefix=/usr dist/yabridge_gui_controller-*.whl
    install -Dm644 src/yabridge-gui-controller.png \
        "\$pkgdir/usr/share/icons/hicolor/256x256/apps/yabridge-gui-controller.png"
    install -Dm644 packaging/specs/yabridge-gui-controller.desktop \
        "\$pkgdir/usr/share/applications/yabridge-gui-controller.desktop"
    install -Dm644 LICENSE \
        "\$pkgdir/usr/share/licenses/\$pkgname/LICENSE"
}
EOF

echo "✓ PKGBUILD written to $PKGBUILD_DIR/PKGBUILD"
echo "  sha256: $SHA256"
echo "  Note: update source= URL and sha256sums after pushing the GitHub tag."

if command -v docker >/dev/null 2>&1; then
    echo "→ Testing PKGBUILD with makepkg in Docker (archlinux)"
    docker run --rm \
        -v "$PKGBUILD_DIR:/build:z" \
        archlinux:latest \
        bash -euo pipefail -c "
            pacman -Sy --noconfirm base-devel python-pip python-setuptools 2>/dev/null
            useradd -m builder
            cp /build/PKGBUILD /home/builder/
            cp /build/yabridge-gui-controller-$VERSION.tar.gz /home/builder/
            chown -R builder /home/builder/
            cd /home/builder
            sed -i 's|source=(.*)|source=(\"yabridge-gui-controller-$VERSION.tar.gz\")|' PKGBUILD
            sudo -u builder makepkg --noconfirm --nodeps -f
            find /home/builder -name '*.pkg.tar.zst' -exec cp {} /build/ \;
        "
    echo "✓ Arch package in $PKGBUILD_DIR/"
else
    echo "⚠ Docker not found — PKGBUILD generated but not tested"
    echo "  To build: cd $PKGBUILD_DIR && makepkg -si"
fi
