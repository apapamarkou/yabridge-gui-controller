# __   __    _          _     _               ____ _   _ ___
# \ \ / /_ _| |__  _ __(_) __| | __ _  ___   / ___| | | |_ _|
#  \ V / _` | '_ \| '__| |/ _` |/ _` |/ _ \ | |  _| | | || |
#   | | (_| | |_) | |  | | (_| | (_| |  __/ | |_| | |_| || |
#   |_|\__,_|_.__/|_|  |_|\__,_|\__, |\___|  \____|\___/|___|
#                               |___/
#   ____            _             _ _
#  / ___|___  _ __ | |_ _ __ ___ | | | ___ _ __
# | |   / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__|
# | |__| (_) | | | | |_| | | (_) | | |  __/ |
#  \____\___/|_| |_|\__|_|  \___/|_|_|\___|_|
#
# Author: Andrianos Papamarkou
# Licence: GPL3
# https://github.com/apapamarkou/yabridge-gui-controller

"""yabridge/yabridgectl operations."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

YABRIDGE_VERSION = "5.1.1"
YABRIDGE_URL = f"https://github.com/robbert-vdh/yabridge/releases/download/{YABRIDGE_VERSION}/yabridge-{YABRIDGE_VERSION}.tar.gz"
YABRIDGE_DIR = Path.home() / ".local/share/yabridge"

VST_DIRS = [
    Path.home() / ".wine/drive_c/Program Files/Steinberg/VstPlugins",
    Path.home() / ".wine/drive_c/Program Files/Common Files/VST3",
    Path.home() / ".wine/drive_c/Program Files/VSTPlugins",
]


@dataclass
class SyncResult:
    setting_up: int
    new_plugins: int
    skipped: int
    raw_output: str


def get_yabridgectl_version() -> str | None:
    for cmd in ["yabridgectl", str(YABRIDGE_DIR / "yabridgectl")]:
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return (r.stdout + r.stderr).strip().splitlines()[0]
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            continue
    return None


def get_yabridge_version() -> str | None:
    lib = YABRIDGE_DIR / "libyabridge-chainloader-vst2.so"
    if lib.exists():
        return YABRIDGE_VERSION  # version embedded in path
    return None


def sync_plugins() -> SyncResult:
    """Run yabridgectl sync and return parsed results."""
    cmd = "yabridgectl"
    if not _which(cmd):
        local = YABRIDGE_DIR / "yabridgectl"
        if local.exists():
            cmd = str(local)
        else:
            raise FileNotFoundError("yabridgectl not found")

    result = subprocess.run([cmd, "sync"], check=True, text=True, capture_output=True, timeout=120)
    output = result.stdout + result.stderr
    return _parse_sync_output(output)


def _parse_sync_output(output: str) -> SyncResult:
    import re

    def _find(pattern: str) -> int:
        m = re.search(pattern, output)
        return int(m.group(1)) if m else 0

    return SyncResult(
        setting_up=_find(r"setting up (\d+)"),
        new_plugins=_find(r"(\d+) new"),
        skipped=_find(r"skipped (\d+)"),
        raw_output=output,
    )


def get_vst_plugins(plugin_dir: Path) -> list[str]:
    """Return plugin names (without extension) from a yabridge directory."""
    if not plugin_dir.exists():
        return []
    plugins = []
    for entry in plugin_dir.iterdir():
        name = entry.name
        if ".vst" in name or ".vst3" in name:
            plugins.append(entry.stem)
    return sorted(plugins)


def create_vst_dirs() -> list[Path]:
    """Create standard VST directories. Returns list of created dirs."""
    created = []
    for d in VST_DIRS:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


def configure_yabridge_paths() -> None:
    """Add standard VST dirs to yabridgectl and set yabridge path."""
    cmd = "yabridgectl"
    if not _which(cmd):
        local = YABRIDGE_DIR / "yabridgectl"
        if local.exists():
            cmd = str(local)
        else:
            raise FileNotFoundError("yabridgectl not found")

    for d in VST_DIRS:
        subprocess.run([cmd, "add", str(d)], check=False, capture_output=True)

    subprocess.run([cmd, "set", "--path-auto"], check=True, capture_output=True)


def _which(cmd: str) -> bool:
    import shutil

    return shutil.which(cmd) is not None
