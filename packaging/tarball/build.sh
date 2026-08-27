#!/usr/bin/env bash
# Build .tar.gz portable package
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VERSION="${1:-$(python3 -c "import sys; sys.path.insert(0,'$ROOT/src'); from yabridge_gui import __version__; print(__version__)" 2>/dev/null || echo "2.0.0")}"
ARCH="$(uname -m)"
PKG_NAME="yabridge-gui-controller"
STAGE="$ROOT/dist/tarball/${PKG_NAME}-${VERSION}"

echo "Building tarball: ${PKG_NAME}-${VERSION}-${ARCH}.tar.gz"

mkdir -p "$STAGE"

# Copy source package
cp -r "$ROOT/src/yabridge_gui" "$STAGE/"
cp -r "$ROOT/database" "$STAGE/" 2>/dev/null || true
cp "$ROOT"/*.md "$STAGE/" 2>/dev/null || true
cp "$ROOT/LICENSE" "$STAGE/" 2>/dev/null || true
cp "$ROOT/src/yabridge-gui-controller.png" "$STAGE/" 2>/dev/null || true

# Launcher
cat > "$STAGE/yabridge-gui-controller" <<'EOF'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
exec python3 -m yabridge_gui "$@"
EOF
chmod +x "$STAGE/yabridge-gui-controller"

# Install script
cat > "$STAGE/install.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.local"
PKG_NAME="yabridge-gui-controller"

mkdir -p "$DEST/bin" "$DEST/share/applications" "$DEST/share/icons" \
         "$DEST/lib/python3/$PKG_NAME" "$DEST/share/$PKG_NAME"

cp -r "$SCRIPT_DIR/yabridge_gui" "$DEST/lib/python3/$PKG_NAME/"
cp -r "$SCRIPT_DIR/database" "$DEST/share/$PKG_NAME/" 2>/dev/null || true

cat > "$DEST/bin/$PKG_NAME" <<LAUNCHER
#!/usr/bin/env bash
export PYTHONPATH="$DEST/lib/python3/$PKG_NAME:\$PYTHONPATH"
exec python3 -m yabridge_gui "\$@"
LAUNCHER
chmod +x "$DEST/bin/$PKG_NAME"

if [ -f "$SCRIPT_DIR/yabridge-gui-controller.png" ]; then
    cp "$SCRIPT_DIR/yabridge-gui-controller.png" "$DEST/share/icons/$PKG_NAME.png"
fi

cat > "$DEST/share/applications/$PKG_NAME.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Yabridge GUI Controller
Exec=$DEST/bin/$PKG_NAME
Icon=$DEST/share/icons/$PKG_NAME.png
Terminal=false
Categories=AudioVideo;Audio;Settings;
DESKTOP

echo "Installed to $DEST/bin/$PKG_NAME"
EOF
chmod +x "$STAGE/install.sh"

# Uninstall script
cat > "$STAGE/uninstall.sh" <<'EOF'
#!/usr/bin/env bash
DEST="$HOME/.local"
PKG_NAME="yabridge-gui-controller"
rm -f "$DEST/bin/$PKG_NAME"
rm -f "$DEST/share/applications/$PKG_NAME.desktop"
rm -f "$DEST/share/icons/$PKG_NAME.png"
rm -rf "$DEST/lib/python3/$PKG_NAME"
echo "Uninstalled $PKG_NAME"
EOF
chmod +x "$STAGE/uninstall.sh"

mkdir -p "$ROOT/dist"
tar -czf "$ROOT/dist/${PKG_NAME}-${VERSION}-${ARCH}.tar.gz" \
    -C "$ROOT/dist/tarball" "${PKG_NAME}-${VERSION}"

echo "Built: $ROOT/dist/${PKG_NAME}-${VERSION}-${ARCH}.tar.gz"
