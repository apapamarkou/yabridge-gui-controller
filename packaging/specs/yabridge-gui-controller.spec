Name:           yabridge-gui-controller
Version:        2.0.0
Release:        1%{?dist}
Summary:        GUI controller for yabridge — manage Windows VST/VST3 plugins on Linux

License:        GPL-3.0-or-later
URL:            https://github.com/apapamarkou/yabridge-gui-controller
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-pip
Requires:       python3 >= 3.10
Requires:       python3-PyQt6 >= 6.4
Requires:       python3-pyyaml >= 6.0

%description
A GUI controller for yabridge — manage Windows VST/VST3 plugins on Linux.
Provides a plugin browser, one-click sync, Pro Audio Setup Assistant,
guided remediation, a free plugin browser, and diagnostic reports.

%prep
%autosetup

%build
python3 -m pip install --no-build-isolation --prefix=%{buildroot}%{_prefix} .

%install
python3 -m pip install --no-build-isolation --root=%{buildroot} --prefix=%{_prefix} .
install -Dm644 packaging/specs/yabridge-gui-controller.desktop \
    %{buildroot}%{_datadir}/applications/yabridge-gui-controller.desktop
install -Dm644 src/yabridge-gui-controller.png \
    %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/yabridge-gui-controller.png
install -Dm644 LICENSE \
    %{buildroot}%{_datadir}/licenses/%{name}/LICENSE

%post
update-desktop-database %{_datadir}/applications &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :

%postun
update-desktop-database %{_datadir}/applications &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :

%files
%license LICENSE
%doc README.md
%{_bindir}/yabridge-gui-controller
%{python3_sitelib}/yabridge_gui/
%{python3_sitelib}/yabridge_gui_controller-*.dist-info/
%{_datadir}/icons/hicolor/256x256/apps/yabridge-gui-controller.png
%{_datadir}/applications/yabridge-gui-controller.desktop

%changelog
* Wed Jan 01 2025 Andrianos Papamarkou <andrianos@example.com> - 2.0.0-1
- Initial release
