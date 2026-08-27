"""Unit tests for installer plans."""

from __future__ import annotations

from yabridge_gui.core.distro import Distribution
from yabridge_gui.core.installer import (
    AptInstaller,
    DnfInstaller,
    PacmanInstaller,
    UnsupportedInstaller,
    get_installer,
)


def _make_distro(distro_id: str, family: str, version: str = "1.0") -> Distribution:
    return Distribution(
        id=distro_id, name=distro_id, version=version, family=family, supported=True
    )


def test_get_installer_debian():
    d = _make_distro("debian", "debian", "13")
    installer = get_installer(d)
    assert isinstance(installer, AptInstaller)


def test_get_installer_ubuntu():
    d = _make_distro("ubuntu", "debian", "26.04")
    installer = get_installer(d)
    assert isinstance(installer, AptInstaller)


def test_get_installer_fedora():
    d = _make_distro("fedora", "fedora", "44")
    installer = get_installer(d)
    assert isinstance(installer, DnfInstaller)


def test_get_installer_arch():
    d = _make_distro("arch", "arch")
    installer = get_installer(d)
    assert isinstance(installer, PacmanInstaller)


def test_get_installer_unsupported():
    d = Distribution(id="gentoo", name="Gentoo", version="2.14", family="gentoo", supported=False)
    installer = get_installer(d)
    assert isinstance(installer, UnsupportedInstaller)


def test_apt_wine_deps_plan_has_sudo():
    d = _make_distro("debian", "debian", "13")
    plan = AptInstaller(d).plan_install_wine_deps()
    assert plan.requires_sudo is True
    assert any("apt install" in c for c in plan.commands)


def test_apt_ubuntu_uses_libasound2t64():
    d = _make_distro("ubuntu", "debian", "26.04")
    plan = AptInstaller(d).plan_install_wine_deps()
    assert any("libasound2t64" in c for c in plan.commands)


def test_apt_debian_uses_libasound2():
    d = _make_distro("debian", "debian", "13")
    plan = AptInstaller(d).plan_install_wine_deps()
    assert any("libasound2:" in c for c in plan.commands)


def test_dnf_wine_deps_plan():
    d = _make_distro("fedora", "fedora", "44")
    plan = DnfInstaller(d).plan_install_wine_deps()
    assert plan.requires_sudo is True
    assert any("dnf" in c for c in plan.commands)


def test_pacman_wine_deps_plan():
    d = _make_distro("arch", "arch")
    plan = PacmanInstaller(d).plan_install_wine_deps()
    assert any("pacman" in c for c in plan.commands)


def test_yabridge_install_plan_no_sudo():
    d = _make_distro("debian", "debian", "13")
    plan = AptInstaller(d).plan_install_yabridge()
    assert plan.requires_sudo is False
    assert any("yabridge" in c for c in plan.commands)


def test_unsupported_plans_are_manual():
    d = Distribution(id="gentoo", name="Gentoo", version="2.14", family="gentoo", supported=False)
    installer = UnsupportedInstaller(d)
    assert installer.plan_install_wine_deps().is_manual is True
    assert installer.plan_install_pipewire_jack().is_manual is True


def test_rt_limits_plan_is_manual():
    d = _make_distro("debian", "debian", "13")
    plan = AptInstaller(d).plan_configure_rt_limits()
    assert plan.is_manual is True
    assert "@audio" in plan.manual_instructions


def test_profile_plan_is_manual():
    d = _make_distro("debian", "debian", "13")
    plan = AptInstaller(d).plan_configure_profile()
    assert plan.is_manual is True
    assert "WINEFSYNC" in plan.manual_instructions
