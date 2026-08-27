"""Linux distribution detection via /etc/os-release."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_IDS = {"debian", "ubuntu", "fedora", "arch"}

# Map derivative IDs to their parent family
_FAMILY_MAP: dict[str, str] = {
    "debian": "debian",
    "ubuntu": "debian",
    "linuxmint": "debian",
    "pop": "debian",
    "elementary": "debian",
    "fedora": "fedora",
    "rhel": "fedora",
    "centos": "fedora",
    "almalinux": "fedora",
    "rocky": "fedora",
    "arch": "arch",
    "manjaro": "arch",
    "endeavouros": "arch",
    "garuda": "arch",
}

# Explicitly supported distro+version combos
_SUPPORTED_COMBOS: set[tuple[str, str]] = {
    ("debian", "13"),
    ("ubuntu", "26.04"),
    ("fedora", "44"),
    ("arch", ""),  # rolling — no version check
}


@dataclass
class Distribution:
    id: str
    name: str
    version: str
    family: str
    supported: bool
    doc_file: str = ""

    @property
    def package_manager(self) -> str:
        return {"debian": "apt", "fedora": "dnf", "arch": "pacman"}.get(self.family, "unknown")


def _parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if "=" not in line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        result[key] = value.strip('"').strip("'")
    return result


def detect_distribution() -> Distribution:
    data = _parse_os_release()
    raw_id = data.get("ID", "").lower()
    name = data.get("NAME", raw_id or "Unknown")
    version = data.get("VERSION_ID", "")
    family = _FAMILY_MAP.get(raw_id, raw_id)

    # Determine if supported
    if raw_id == "arch":
        supported = True
        doc_file = "arch.md"
    elif (raw_id, version) in _SUPPORTED_COMBOS:
        supported = True
        doc_file = _doc_for(raw_id)
    else:
        # Check major version match for debian/ubuntu/fedora
        major = version.split(".")[0]
        supported = any(
            raw_id == sid and (sv == version or sv.split(".")[0] == major)
            for sid, sv in _SUPPORTED_COMBOS
        )
        doc_file = _doc_for(raw_id) if supported else "others.md"

    return Distribution(
        id=raw_id,
        name=name,
        version=version,
        family=family,
        supported=supported,
        doc_file=doc_file,
    )


def _doc_for(distro_id: str) -> str:
    return {
        "debian": "debian13.md",
        "ubuntu": "ubuntu2604.md",
        "fedora": "fedora44.md",
        "arch": "arch.md",
    }.get(distro_id, "others.md")
