#!/usr/bin/env bash
# Build .rpm package (requires rpmbuild)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VERSION="${1:-$(python3 -c "import sys; sys.path.insert(0,'$ROOT/src'); from yabridge_gui import __version__; print(__version__)" 2>/dev/null || echo "2.0.0")}"
ARCH="$(uname -m)"
PKG_NAME="yabridge-gui-controller"

echo "Building .rpm: ${PKG_NAME}-${VERSION}-${ARCH}.rpm"

# Build sdist first
cd "$ROOT"
python3 -m build --sdist --outdir /tmp/yabridge-sdist/

SDIST="/tmp/yabridge-sdist/${PKG_NAME}-${VERSION}.tar.gz"

# Write spec file
SPEC_FILE="/tmp/${PKG_NAME}.spec"
cat > "$SPEC_FILE" <<EOF
Name:           $PKG_NAME
Version:        $VERSION
Release:        1%{?dist}
Summary:        GUI controller for yabridge — manage Windows VST/VST3 plugins on Linux
License:        GPL-3.0
URL:            https://github.com/apapamarkou/yabridge-gui-controller
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.10, python3-PyQt6, python3-pyyaml

%description
A GUI controller for yabridge — manage Windows VST/VST3 plugins on Linux.

%prep
%setup -q

%install
pip3 install --root=%{buildroot} --prefix=/usr --no-deps .
mkdir -p %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/$PKG_NAME <<'LAUNCHER'
#!/usr/bin/env python3
from yabridge_gui.__main__ import main
main()
LAUNCHER
chmod +x %{buildroot}/usr/bin/$PKG_NAME
mkdir -p %{buildroot}/usr/share/applications
cat > %{buildroot}/usr/share/applications/$PKG_NAME.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Yabridge GUI Controller
Exec=$PKG_NAME
Icon=$PKG_NAME
Terminal=false
Categories=AudioVideo;Audio;Settings;
DESKTOP

%files
/usr/bin/$PKG_NAME
/usr/share/applications/$PKG_NAME.desktop
%{python3_sitelib}/yabridge_gui/
%{python3_sitelib}/yabridge_gui_controller-*.dist-info/

%changelog
* $(date '+%a %b %d %Y') Andrianos Papamarkou <> - $VERSION-1
- Release $VERSION
EOF

mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
cp "$SDIST" ~/rpmbuild/SOURCES/ 2>/dev/null || true
cp "$SPEC_FILE" ~/rpmbuild/SPECS/

rpmbuild -bb ~/rpmbuild/SPECS/"${PKG_NAME}.spec"

mkdir -p "$ROOT/dist"
find ~/rpmbuild/RPMS -name "${PKG_NAME}-${VERSION}*.rpm" -exec cp {} "$ROOT/dist/" \;
echo "Built RPM in $ROOT/dist/"
