#!/usr/bin/env bash
# Build a self-contained fat AppImage using python-appimage.
# Bundles Python 3.11, PyQt6 + Qt6 libs, PyYAML, and yabridge-gui-controller.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(grep '^fallback_version' "$REPO_ROOT/pyproject.toml" | sed 's/.*= *"\(.*\)"/\1/')"
OUTPUT="$REPO_ROOT/packaging/output"

command -v docker >/dev/null 2>&1 || { echo "⚠ docker not found — skipping"; exit 2; }

BUILDER_IMAGE="yabridge-gui-controller-appimage-builder:3"
if ! docker image inspect "$BUILDER_IMAGE" >/dev/null 2>&1; then
    echo "→ Building reusable builder image (one-time, takes a few minutes)"
    DOCKERFILE_DIR="$(mktemp -d /tmp/ybg-docker-XXXXXX)"
    cat > "$DOCKERFILE_DIR/Dockerfile" << 'DOCKEREOF'
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq \
    python3 python3-pip python3-dev wget file patchelf binutils \
    libfuse2 desktop-file-utils squashfs-tools \
    libglib2.0-0 libpcre3 libpcre2-8-0 \
    libxcb-cursor0 libxcb-render-util0 libxcb-image0 libxcb-shm0 libxcb-util1 \
    libxcb1 libxau6 libxdmcp6 libbsd0 libxkbcommon0 libxkbcommon-x11-0 \
    libegl1 libgl1 libdbus-1-3 libx11-6 libx11-xcb1 \
    libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-randr0 \
    libxcb-xfixes0 libxcb-sync1 libxcb-xkb1 libxcb-glx0 \
    && python3 -m pip install --quiet --break-system-packages python-appimage \
    && wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
        -O /tmp/appimagetool.AppImage \
    && chmod +x /tmp/appimagetool.AppImage \
    && /tmp/appimagetool.AppImage --appimage-extract \
    && mv squashfs-root /opt/appimagetool \
    && ln -sf /opt/appimagetool/AppRun /usr/local/bin/appimagetool \
    && rm /tmp/appimagetool.AppImage \
    && rm -rf /var/lib/apt/lists/*
DOCKEREOF
    docker build --load -t "$BUILDER_IMAGE" -f "$DOCKERFILE_DIR/Dockerfile" "$DOCKERFILE_DIR"
    rm -rf "$DOCKERFILE_DIR"
fi

mkdir -p "$OUTPUT"

WHEEL_DIR="$(mktemp -d)"
APPIMG_META="$(mktemp -d)"
INNER="$(mktemp)"
trap 'rm -rf "$WHEEL_DIR" "$APPIMG_META" "$INNER"' EXIT

python3 -m pip wheel "$REPO_ROOT" --no-deps -w "$WHEEL_DIR" -q
WHEEL_NAME="$(basename "$WHEEL_DIR"/yabridge_gui_controller-*.whl)"

echo "→ Pre-downloading dependency wheels on host"
python3 -m pip download PyQt6 PyQt6-sip PyQt6-Qt6 PyYAML -d "$WHEEL_DIR" -q

cat > "$APPIMG_META/requirements.txt" << EOF
PyQt6>=6.4
PyYAML>=6.0
local+yabridge_gui
EOF

cat > "$APPIMG_META/entrypoint.sh" << 'EOF'
#! /bin/bash
QT6LIB="${APPDIR}/opt/python3.11/lib/python3.11/site-packages/PyQt6/Qt6/lib"
export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${QT6LIB}"
"${APPDIR}/usr/bin/python3" -m yabridge_gui "$@"
EOF

# Use a space-free Name= so python-appimage produces a clean filename
cp "$REPO_ROOT/packaging/specs/yabridge-gui-controller.desktop" "$APPIMG_META/"
sed -i 's/^Name=.*/Name=YabridgeGUIController/' "$APPIMG_META/yabridge-gui-controller.desktop"
cp "$REPO_ROOT/src/yabridge-gui-controller.png" "$APPIMG_META/"

cat > "$INNER" << INNEREOF
#!/usr/bin/env bash
set -euo pipefail

# Patch python-appimage: pre-downloaded wheels + pre-installed appimagetool
python3 << 'PYEOF'
import python_appimage.commands.build.app as m
import python_appimage.utils.deps as d
import inspect, re

src = inspect.getfile(m)
with open(src) as f:
    code = f.read()
patched = re.sub(
    r"(system\(\('./AppDir/AppRun'[^)]*?'pip'[^)]*?'install'[^)]*?in_tree_build,)",
    r"\1 '--find-links', '/wheels',",
    code, flags=re.DOTALL
)
with open(src, 'w') as f:
    f.write(patched)

src2 = inspect.getfile(d)
with open(src2) as f:
    code2 = f.read()
patched2 = re.sub(
    r'def ensure_appimagetool\(.*?\):[\s\S]*?(?=^def |^class )',
    'def ensure_appimagetool(dry=False):\n    return "/opt/appimagetool/AppRun"\n\n',
    code2, flags=re.DOTALL | re.MULTILINE
)
with open(src2, 'w') as f:
    f.write(patched2)
print('python-appimage patched')
PYEOF

pip3 install --quiet --root-user-action=ignore --break-system-packages --no-deps \
    --target=/tmp/yabridge-pkg /wheels/$WHEEL_NAME
export PYTHONPATH=/tmp/yabridge-pkg

WORKDIR=/tmp/appimage-work
mkdir -p \$WORKDIR
cp -r /appmeta/. \$WORKDIR/appdir/

cd \$WORKDIR
python3 -m python_appimage build app --python-version 3.11 --name YabridgeGUIController appdir

# python-appimage produces YabridgeGUIController-x86_64.AppImage (no version)
BUILT=\$(ls \$WORKDIR/YabridgeGUIController-*.AppImage 2>/dev/null | head -1)
echo "→ Extracting \$(basename \$BUILT) to add system libraries"
chmod +x "\$BUILT"
"\$BUILT" --appimage-extract
APPDIR=\$WORKDIR/squashfs-root

# Remove libs that must come from the host (glibc, lzma)
rm -f \$APPDIR/usr/lib/libc.so* \$APPDIR/usr/lib/libm.so* \$APPDIR/usr/lib/libdl.so* \
       \$APPDIR/usr/lib/libpthread.so* \$APPDIR/usr/lib/librt.so* \$APPDIR/usr/lib/libutil.so* \
       \$APPDIR/usr/lib/ld-linux*.so* \$APPDIR/usr/lib/liblzma.so*

mkdir -p \$APPDIR/usr/lib

for lib in \
    libglib-2.0.so.0 libgthread-2.0.so.0 libgmodule-2.0.so.0 libgobject-2.0.so.0 \
    libpcre.so.3 libpcre2-8.so.0 \
    libxcb-cursor.so.0 libxcb-render-util.so.0 libxcb-render.so.0 \
    libxcb-image.so.0 libxcb-shm.so.0 libxcb-util.so.1 \
    libxcb.so.1 libXau.so.6 libXdmcp.so.6 libbsd.so.0 libmd.so.0 \
    libxkbcommon.so.0 libxkbcommon-x11.so.0 \
    libdbus-1.so.3; do
    src=\$(find /usr/lib /usr/lib/x86_64-linux-gnu /lib /lib/x86_64-linux-gnu -name "\$lib" 2>/dev/null | head -1 || true)
    [ -n "\$src" ] && cp -L "\$src" \$APPDIR/usr/lib/ && echo "  bundled \$lib" || echo "  ⚠ not found: \$lib"
done

SKIP_PATTERN='/(libc|libm|libdl|libpthread|librt|libresolv|libnss|libutil|ld-linux|libgcc_s|liblzma)\.so'
find \$APPDIR/opt/python3.11/lib/python3.11/site-packages/PyQt6 -name '*.so*' | while read -r so; do
    ldd "\$so" 2>/dev/null | awk '/=> \//{print \$3}' | while read -r dep; do
        [[ "\$dep" == \$APPDIR/* ]] && continue
        echo "\$dep" | grep -qE "\$SKIP_PATTERN" && continue
        [ -f "\$dep" ] && cp -Ln "\$dep" \$APPDIR/usr/lib/ 2>/dev/null || true
    done
done

if [ ! -f \$APPDIR/usr/lib/libxcb-cursor.so.0 ]; then
    echo "✗ libxcb-cursor.so.0 not found — cannot bundle" >&2
    exit 1
fi

XCB_PLUGIN=\$(find \$APPDIR -name "libqxcb.so" 2>/dev/null | head -1)
if [ -n "\$XCB_PLUGIN" ]; then
    patchelf --set-rpath '\$ORIGIN/../../../../../../../../../usr/lib' "\$XCB_PLUGIN"
fi

sed -i 's|# Call the application entry point|QT6LIB="\${APPDIR}/opt/python3.11/lib/python3.11/site-packages/PyQt6/Qt6/lib"\nexport LD_LIBRARY_PATH="\${APPDIR}/usr/lib:\${QT6LIB}"\n# Call the application entry point|' \$APPDIR/AppRun

echo "→ Repacking as YabridgeGUIController-${VERSION}-x86_64.AppImage"
ARCH=x86_64 /opt/appimagetool/AppRun --no-appstream \$APPDIR /output/YabridgeGUIController-${VERSION}-x86_64.AppImage
echo "Done"
INNEREOF

echo "→ Building fat AppImage in Docker (takes a few minutes)"
docker run --rm \
    --privileged \
    --network host \
    -v "$REPO_ROOT:/src:ro,z" \
    -v "$OUTPUT:/output:z" \
    -v "$WHEEL_DIR:/wheels:ro,z" \
    -v "$APPIMG_META:/appmeta:ro,z" \
    -v "$INNER:/build-inner.sh:ro,z" \
    "$BUILDER_IMAGE" \
    bash /build-inner.sh

echo "✓ Fat AppImage in $OUTPUT/"
