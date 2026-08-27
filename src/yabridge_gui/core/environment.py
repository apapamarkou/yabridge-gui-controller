"""Environment checks for pro-audio setup."""

from __future__ import annotations

import grp
import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CheckStatus(Enum):
    OK = "ok"
    MISSING = "missing"
    WARNING = "warning"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


@dataclass
class EnvironmentCheck:
    name: str
    label: str
    status: CheckStatus
    detail: str = ""
    fix_available: bool = False
    fix_key: str = ""


def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False, ""


def _command_version(cmd: str, flag: str = "--version") -> tuple[bool, str]:
    ok, out = _run([cmd, flag])
    return ok, out.splitlines()[0] if out else ""


def check_wine() -> EnvironmentCheck:
    ok, ver = _command_version("wine")
    if ok:
        return EnvironmentCheck("wine", "Wine", CheckStatus.OK, ver)
    # Check user-local install
    local_wine = Path.home() / ".local/share/wine-staging-9.21/bin/wine"
    if local_wine.exists():
        ok2, ver2 = _run([str(local_wine), "--version"])
        if ok2:
            return EnvironmentCheck("wine", "Wine", CheckStatus.OK, ver2)
    return EnvironmentCheck(
        "wine",
        "Wine",
        CheckStatus.MISSING,
        "Not found in PATH",
        fix_available=True,
        fix_key="install_wine",
    )


def check_yabridge() -> EnvironmentCheck:
    ok, ver = _command_version("yabridgectl")
    if ok:
        return EnvironmentCheck("yabridgectl", "yabridgectl", CheckStatus.OK, ver)
    local = Path.home() / ".local/share/yabridge/yabridgectl"
    if local.exists():
        ok2, ver2 = _run([str(local), "--version"])
        if ok2:
            return EnvironmentCheck("yabridgectl", "yabridgectl", CheckStatus.OK, ver2)
    return EnvironmentCheck(
        "yabridgectl",
        "yabridgectl",
        CheckStatus.MISSING,
        "Not found",
        fix_available=True,
        fix_key="install_yabridge",
    )


def check_yabridge_binary() -> EnvironmentCheck:
    paths = [
        Path.home() / ".local/share/yabridge/libyabridge-chainloader-vst2.so",
        Path.home() / ".local/share/yabridge/libyabridge-chainloader-vst3.so",
    ]
    if any(p.exists() for p in paths):
        return EnvironmentCheck("yabridge", "yabridge", CheckStatus.OK, str(paths[0].parent))
    return EnvironmentCheck(
        "yabridge",
        "yabridge",
        CheckStatus.MISSING,
        "Not found in ~/.local/share/yabridge",
        fix_available=True,
        fix_key="install_yabridge",
    )


def check_audio_group() -> EnvironmentCheck:
    username = os.getenv("USER") or os.getenv("LOGNAME") or ""
    try:
        audio_group = grp.getgrnam("audio")
        if username in audio_group.gr_mem:
            return EnvironmentCheck(
                "audio_group", "Audio group", CheckStatus.OK, f"User '{username}' in audio group"
            )
        return EnvironmentCheck(
            "audio_group",
            "Audio group",
            CheckStatus.WARNING,
            f"User '{username}' not in audio group",
            fix_available=False,
            fix_key="add_audio_group",
        )
    except KeyError:
        return EnvironmentCheck(
            "audio_group", "Audio group", CheckStatus.UNKNOWN, "audio group not found"
        )


def check_realtime_limits() -> EnvironmentCheck:
    limits_file = Path("/etc/security/limits.conf")
    if not limits_file.exists():
        return EnvironmentCheck(
            "rt_limits", "Realtime limits", CheckStatus.UNKNOWN, "/etc/security/limits.conf missing"
        )
    content = limits_file.read_text()
    has_rtprio = "@audio" in content and "rtprio" in content
    has_memlock = "@audio" in content and "memlock" in content
    if has_rtprio and has_memlock:
        return EnvironmentCheck(
            "rt_limits", "Realtime limits", CheckStatus.OK, "rtprio + memlock configured"
        )
    return EnvironmentCheck(
        "rt_limits",
        "Realtime limits",
        CheckStatus.WARNING,
        "Missing @audio rtprio/memlock in /etc/security/limits.conf",
        fix_available=False,
        fix_key="configure_rt_limits",
    )


def check_pipewire() -> EnvironmentCheck:
    ok, ver = _command_version("pipewire")
    if not ok:
        return EnvironmentCheck("pipewire", "PipeWire", CheckStatus.MISSING, "pipewire not found")
    # Check JACK compatibility
    jack_ok, _ = _run(["pw-jack", "--version"])
    if jack_ok:
        return EnvironmentCheck("pipewire", "PipeWire/JACK", CheckStatus.OK, ver)
    return EnvironmentCheck(
        "pipewire",
        "PipeWire/JACK",
        CheckStatus.WARNING,
        f"{ver} — JACK bridge (pw-jack) not available",
        fix_available=True,
        fix_key="install_pipewire_jack",
    )


def check_wireplumber() -> EnvironmentCheck:
    ok, _ = _run(["systemctl", "--user", "is-active", "wireplumber.service"])
    if ok:
        return EnvironmentCheck("wireplumber", "WirePlumber", CheckStatus.OK, "service active")
    ok2, _ = _command_version("wireplumber")
    if ok2:
        return EnvironmentCheck(
            "wireplumber",
            "WirePlumber",
            CheckStatus.WARNING,
            "Installed but service not active",
            fix_available=True,
            fix_key="enable_wireplumber",
        )
    return EnvironmentCheck("wireplumber", "WirePlumber", CheckStatus.MISSING, "Not found")


def check_vst_dirs() -> EnvironmentCheck:
    dirs = [
        Path.home() / ".wine/drive_c/Program Files/Steinberg/VstPlugins",
        Path.home() / ".wine/drive_c/Program Files/Common Files/VST3",
        Path.home() / ".wine/drive_c/Program Files/VSTPlugins",
    ]
    missing = [str(d) for d in dirs if not d.exists()]
    if not missing:
        return EnvironmentCheck("vst_dirs", "VST directories", CheckStatus.OK, "All present")
    return EnvironmentCheck(
        "vst_dirs",
        "VST directories",
        CheckStatus.WARNING,
        f"Missing: {', '.join(missing)}",
        fix_available=True,
        fix_key="create_vst_dirs",
    )


def check_yabridge_paths() -> EnvironmentCheck:
    ok, out = _run(["yabridgectl", "status"])
    if not ok:
        # Try local binary
        local = Path.home() / ".local/share/yabridge/yabridgectl"
        if local.exists():
            ok, out = _run([str(local), "status"])
    if ok and out:
        return EnvironmentCheck(
            "yabridge_paths", "yabridge paths", CheckStatus.OK, "Paths configured"
        )
    return EnvironmentCheck(
        "yabridge_paths",
        "yabridge paths",
        CheckStatus.WARNING,
        "No paths configured in yabridgectl",
        fix_available=True,
        fix_key="configure_yabridge_paths",
    )


def check_profile_paths() -> EnvironmentCheck:
    profile = Path.home() / ".profile"
    if not profile.exists():
        return EnvironmentCheck(
            "profile_paths", "PATH (yabridge/wine)", CheckStatus.WARNING, "~/.profile not found"
        )
    content = profile.read_text()
    has_yabridge = ".local/share/yabridge" in content
    has_wine = "wine-staging" in content
    has_winefsync = "WINEFSYNC" in content
    if has_yabridge and has_wine and has_winefsync:
        return EnvironmentCheck(
            "profile_paths", "PATH (yabridge/wine)", CheckStatus.OK, "~/.profile configured"
        )
    missing = []
    if not has_yabridge:
        missing.append("yabridge path")
    if not has_wine:
        missing.append("wine-staging path")
    if not has_winefsync:
        missing.append("WINEFSYNC=1")
    return EnvironmentCheck(
        "profile_paths",
        "PATH (yabridge/wine)",
        CheckStatus.WARNING,
        f"~/.profile missing: {', '.join(missing)}",
        fix_available=False,
        fix_key="configure_profile",
    )


def run_environment_checks() -> list[EnvironmentCheck]:
    return [
        check_wine(),
        check_yabridge_binary(),
        check_yabridge(),
        check_vst_dirs(),
        check_yabridge_paths(),
        check_profile_paths(),
        check_audio_group(),
        check_realtime_limits(),
        check_pipewire(),
        check_wireplumber(),
    ]
