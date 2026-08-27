#!/usr/bin/env bash
# Build AppImage (requires appimagetool)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VERSION="${1:-$(python3 -c "import sys; sys.path.insert(0,'$ROOT/src'); from yabridge_gui import __version__; print(__version__)" 2>/dev/null || echo "2.0.0")}"
ARCH="$(uname -m)"
PKG_NAME="yabridge-gui-controller"
APPDIR="$ROOT/dist/appimage/${PKG_NAME}.AppDir"

echo "Building AppImage: ${PKG_NAME}-${VERSION}-${ARCH}.AppImage"

# Check for appimagetool
if ! command -v appimagetool &>/dev/null; then
    echo "appimagetool not found. Downloading..."
    TOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    curl -L -o /tmp/appimagetool "$TOOL_URL"
    chmod +x /tmp/appimagetool
    APPIMAGETOOL=/tmp/appimagetool
else
    APPIMAGETOOL=appimagetool
fi

mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Install Python package into AppDir
pip3 install --quiet --target "$APPDIR/usr/lib/python3" --no-deps "$ROOT"

# Copy database
cp -r "$ROOT/database" "$APPDIR/usr/share/$PKG_NAME/" 2>/dev/null || true

# AppRun
cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="$HERE/usr/lib/python3:$PYTHONPATH"
exec python3 -m yabridge_gui "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Desktop entry
cat > "$APPDIR/$PKG_NAME.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Yabridge GUI Controller
Exec=$PKG_NAME
Icon=$PKG_NAME
Terminal=false
Categories=AudioVideo;Audio;Settings;
EOF
cp "$APPDIR/$PKG_NAME.desktop" "$APPDIR/usr/share/applications/"

# Icon
if [ -f "$ROOT/src/yabridge-gui-controller.png" ]; then
    cp "$ROOT/src/yabridge-gui-controller.png" \
       "$APPDIR/usr/share/icons/hicolor/256x256/apps/$PKG_NAME.png"
    cp "$ROOT/src/yabridge-gui-controller.png" "$APPDIR/$PKG_NAME.png"
fi

mkdir -p "$ROOT/dist"
ARCH="$ARCH" "$APPIMAGETOOL" "$APPDIR" \
    "$ROOT/dist/${PKG_NAME}-${VERSION}-${ARCH}.AppImage"

echo "Built: $ROOT/dist/${PKG_NAME}-${VERSION}-${ARCH}.AppImage"
