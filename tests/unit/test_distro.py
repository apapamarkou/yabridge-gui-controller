"""Unit tests for distribution detection."""

from __future__ import annotations

from unittest.mock import mock_open, patch

from yabridge_gui.core.distro import (
    Distribution,
    _parse_os_release,
    detect_distribution,
)

OS_RELEASE_UBUNTU = """
ID=ubuntu
NAME="Ubuntu"
VERSION_ID="26.04"
"""

OS_RELEASE_DEBIAN = """
ID=debian
NAME="Debian GNU/Linux"
VERSION_ID="13"
"""

OS_RELEASE_FEDORA = """
ID=fedora
NAME="Fedora Linux"
VERSION_ID="44"
"""

OS_RELEASE_ARCH = """
ID=arch
NAME="Arch Linux"
"""

OS_RELEASE_UNKNOWN = """
ID=gentoo
NAME="Gentoo"
VERSION_ID="2.14"
"""


def _mock_detect(content: str) -> Distribution:
    with (
        patch("builtins.open", mock_open(read_data=content)),
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value=content),
    ):
        return detect_distribution()


def test_parse_os_release_basic():
    content = 'ID=ubuntu\nNAME="Ubuntu"\nVERSION_ID="26.04"\n'
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value=content),
    ):
        result = _parse_os_release()
    assert result["ID"] == "ubuntu"
    assert result["VERSION_ID"] == "26.04"


def test_parse_os_release_missing_file():
    with patch("pathlib.Path.exists", return_value=False):
        result = _parse_os_release()
    assert result == {}


def test_ubuntu_detected():
    distro = _mock_detect(OS_RELEASE_UBUNTU)
    assert distro.id == "ubuntu"
    assert distro.version == "26.04"
    assert distro.family == "debian"
    assert distro.supported is True
    assert distro.package_manager == "apt"


def test_debian_detected():
    distro = _mock_detect(OS_RELEASE_DEBIAN)
    assert distro.id == "debian"
    assert distro.version == "13"
    assert distro.family == "debian"
    assert distro.supported is True


def test_fedora_detected():
    distro = _mock_detect(OS_RELEASE_FEDORA)
    assert distro.id == "fedora"
    assert distro.version == "44"
    assert distro.family == "fedora"
    assert distro.supported is True
    assert distro.package_manager == "dnf"


def test_arch_detected():
    distro = _mock_detect(OS_RELEASE_ARCH)
    assert distro.id == "arch"
    assert distro.family == "arch"
    assert distro.supported is True
    assert distro.package_manager == "pacman"


def test_unknown_distro_unsupported():
    distro = _mock_detect(OS_RELEASE_UNKNOWN)
    assert distro.supported is False
    assert distro.doc_file == "others.md"


def test_distribution_dataclass():
    d = Distribution(
        id="ubuntu",
        name="Ubuntu",
        version="26.04",
        family="debian",
        supported=True,
        doc_file="ubuntu2604.md",
    )
    assert d.package_manager == "apt"
