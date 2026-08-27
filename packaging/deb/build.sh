#!/usr/bin/env bash
# Build .deb package
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VERSION="${1:-$(python3 -c "import sys; sys.path.insert(0,'$ROOT/src'); from yabridge_gui import __version__; print(__version__)" 2>/dev/null || echo "2.0.0")}"
ARCH="$(dpkg --print-architecture 2>/dev/null || echo "amd64")"
PKG_NAME="yabridge-gui-controller"
PKG_DIR="$ROOT/dist/deb/${PKG_NAME}_${VERSION}_${ARCH}"

echo "Building .deb: ${PKG_NAME}_${VERSION}_${ARCH}.deb"

# Create package tree
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/usr/share/doc/$PKG_NAME"
mkdir -p "$PKG_DIR/usr/share/$PKG_NAME/database"
mkdir -p "$PKG_DIR/usr/lib/python3/dist-packages"

# Install Python package
pip3 install --quiet --target "$PKG_DIR/usr/lib/python3/dist-packages" \
    --no-deps "$ROOT"

# Launcher script
cat > "$PKG_DIR/usr/bin/$PKG_NAME" <<'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, "/usr/lib/python3/dist-packages")
from yabridge_gui.__main__ import main
main()
EOF
chmod +x "$PKG_DIR/usr/bin/$PKG_NAME"

# Desktop entry
cat > "$PKG_DIR/usr/share/applications/$PKG_NAME.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Yabridge GUI Controller
Comment=Manage Windows VST/VST3 plugins via yabridge
Exec=$PKG_NAME
Icon=$PKG_NAME
Terminal=false
Categories=AudioVideo;Audio;Settings;
StartupNotify=true
EOF

# Icon
if [ -f "$ROOT/src/yabridge-gui-controller.png" ]; then
    cp "$ROOT/src/yabridge-gui-controller.png" \
       "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/$PKG_NAME.png"
fi

# Database
if [ -d "$ROOT/database" ]; then
    cp -r "$ROOT/database" "$PKG_DIR/usr/share/$PKG_NAME/"
fi

# Docs
cp "$ROOT"/*.md "$PKG_DIR/usr/share/doc/$PKG_NAME/" 2>/dev/null || true

# Control file
INSTALLED_SIZE=$(du -sk "$PKG_DIR" | cut -f1)
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: Andrianos Papamarkou
Installed-Size: $INSTALLED_SIZE
Depends: python3 (>= 3.10), python3-pyqt6, python3-yaml
Description: Yabridge GUI Controller
 A GUI controller for yabridge — manage Windows VST/VST3 plugins on Linux.
EOF

# Build
mkdir -p "$ROOT/dist"
dpkg-deb --build "$PKG_DIR" "$ROOT/dist/${PKG_NAME}-${VERSION}-${ARCH}.deb"
echo "Built: $ROOT/dist/${PKG_NAME}-${VERSION}-${ARCH}.deb"
