#!/usr/bin/env bash
# Build an AppImage inside a reusable Docker builder image.
# appimagetool is pre-installed as a plain binary — no FUSE needed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(python3 -c "import sys; sys.path.insert(0,'$REPO_ROOT/src'); from yabridge_gui import __version__; print(__version__)" 2>/dev/null || echo "2.0.0")"
OUTPUT="$REPO_ROOT/packaging/output"
CONF="$REPO_ROOT/packaging/distro-versions.conf"

UBUNTU_VER="$(grep '^ubuntu-versions=' "$CONF" | cut -d= -f2 | tr ',' '\n' | tail -1)"

command -v docker >/dev/null 2>&1 || { echo "⚠ docker not found — skipping"; exit 2; }

# Build reusable builder image if not already present
BUILDER_IMAGE="yabridge-gui-controller-appimage-builder:1"
if ! docker image inspect "$BUILDER_IMAGE" >/dev/null 2>&1; then
    echo "→ Building reusable builder image (one-time)"
    DOCKERFILE_DIR="$(mktemp -d -p "$REPO_ROOT/packaging")"
    DOCKERFILE="$DOCKERFILE_DIR/Dockerfile"
    cat > "$DOCKERFILE" <<DOCKEREOF
FROM ubuntu:${UBUNTU_VER}
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq \\
    python3 python3-pip wget file squashfs-tools \\
    libglib2.0-0 libfuse2 \\
    && wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \\
        -O /tmp/appimagetool.AppImage \\
    && chmod +x /tmp/appimagetool.AppImage \\
    && /tmp/appimagetool.AppImage --appimage-extract \\
    && mv squashfs-root /opt/appimagetool \\
    && ln -s /opt/appimagetool/AppRun /usr/local/bin/appimagetool \\
    && rm /tmp/appimagetool.AppImage \\
    && rm -rf /var/lib/apt/lists/*
DOCKEREOF
    docker build --load -t "$BUILDER_IMAGE" -f "$DOCKERFILE" "$DOCKERFILE_DIR"
    rm -rf "$DOCKERFILE_DIR"
fi

mkdir -p "$OUTPUT"

echo "→ Building AppImage in Docker"

WHEEL_DIR="$(mktemp -d)"
python3 -m pip wheel "$REPO_ROOT" --no-deps -w "$WHEEL_DIR" -q

PKG_NAME="yabridge-gui-controller"

INNER="$(mktemp -p "$REPO_ROOT/packaging")"
cat > "$INNER" <<'INNEREOF'
#!/usr/bin/env bash
set -euo pipefail

APPDIR=/tmp/appdir/yabridge-gui-controller.AppDir
mkdir -p $APPDIR/usr/bin $APPDIR/usr/share/applications \
         $APPDIR/usr/share/icons/hicolor/256x256/apps \
         $APPDIR/usr/lib/python3

WHEEL=$(ls /wheels/yabridge_gui_controller-*.whl /wheels/yabridge-gui-controller-*.whl 2>/dev/null | head -1)
pip3 install --quiet --target $APPDIR/usr/lib/python3 --no-deps "$WHEEL"

[ -d /src/database ] && cp -r /src/database $APPDIR/usr/share/yabridge-gui-controller/ || true

cat > $APPDIR/AppRun <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="$HERE/usr/lib/python3:$PYTHONPATH"
exec python3 -m yabridge_gui "$@"
EOF
chmod +x $APPDIR/AppRun

cat > $APPDIR/yabridge-gui-controller.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Yabridge GUI Controller
Exec=yabridge-gui-controller
Icon=yabridge-gui-controller
Terminal=false
Categories=AudioVideo;Audio;Settings;
EOF
cp $APPDIR/yabridge-gui-controller.desktop $APPDIR/usr/share/applications/

[ -f /src/src/yabridge-gui-controller.png ] && \
    cp /src/src/yabridge-gui-controller.png \
       $APPDIR/usr/share/icons/hicolor/256x256/apps/yabridge-gui-controller.png && \
    cp /src/src/yabridge-gui-controller.png $APPDIR/yabridge-gui-controller.png || true

ARCH=x86_64 appimagetool $APPDIR /output/YabridgeGUIController-${VERSION}-x86_64.AppImage
echo "Built AppImage in /output/"
INNEREOF

# Inject VERSION into inner script
sed -i "s/\${VERSION}/$VERSION/g" "$INNER"

docker run --rm \
    -v "$REPO_ROOT:/src:ro,z" \
    -v "$OUTPUT:/output:z" \
    -v "$WHEEL_DIR:/wheels:ro,z" \
    -v "$INNER:/build-inner.sh:ro,z" \
    "$BUILDER_IMAGE" \
    bash /build-inner.sh

rm -rf "$WHEEL_DIR" "$INNER"
echo "✓ AppImage in $OUTPUT/"
