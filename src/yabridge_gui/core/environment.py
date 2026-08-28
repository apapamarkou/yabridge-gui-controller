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
    logout_warning: str = ""


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


def check_wine_configured() -> EnvironmentCheck:
    """Check whether winetricks and winecfg have been run (Wine prefix exists)."""
    wineprefix = Path.home() / ".wine"
    system32 = wineprefix / "drive_c/windows/system32"
    # A configured Wine prefix always has drive_c/windows/system32
    if system32.exists():
        return EnvironmentCheck(
            "wine_configured", "Wine configured", CheckStatus.OK, "Wine prefix found"
        )
    return EnvironmentCheck(
        "wine_configured",
        "Wine configured",
        CheckStatus.WARNING,
        "Wine prefix not initialised — run winetricks + winecfg",
        fix_available=True,
        fix_key="configure_wine",
    )


def check_yabridge() -> EnvironmentCheck:
    """Single check covering both the yabridge binaries and yabridgectl."""
    binary_paths = [
        Path.home() / ".local/share/yabridge/libyabridge-chainloader-vst2.so",
        Path.home() / ".local/share/yabridge/libyabridge-chainloader-vst3.so",
    ]
    has_binary = any(p.exists() for p in binary_paths)

    ok, ver = _command_version("yabridgectl")
    if not ok:
        local = Path.home() / ".local/share/yabridge/yabridgectl"
        if local.exists():
            ok, ver = _run([str(local), "--version"])
            ver = ver.splitlines()[0] if ver else ""
    has_ctl = ok

    if has_binary and has_ctl:
        return EnvironmentCheck("yabridge", "yabridge", CheckStatus.OK, ver)
    missing = []
    if not has_binary:
        missing.append("binaries")
    if not has_ctl:
        missing.append("yabridgectl")
    return EnvironmentCheck(
        "yabridge",
        "yabridge",
        CheckStatus.MISSING,
        f"Missing: {', '.join(missing)}",
        fix_available=True,
        fix_key="install_yabridge",
    )


def check_audio_group() -> EnvironmentCheck:
    username = os.getenv("USER") or os.getenv("LOGNAME") or ""
    try:
        audio_group = grp.getgrnam("audio")
        if username in audio_group.gr_mem:
            result = subprocess.run(["id", "-Gn"], capture_output=True, text=True)
            active_groups = result.stdout.split()
            if "audio" not in active_groups:
                return EnvironmentCheck(
                    "audio_group",
                    "Audio group",
                    CheckStatus.WARNING,
                    f"User '{username}' in audio group but session not updated",
                    logout_warning="Logout or restart required for audio group membership to take effect.",
                )
            return EnvironmentCheck(
                "audio_group", "Audio group", CheckStatus.OK, f"User '{username}' in audio group"
            )
        return EnvironmentCheck(
            "audio_group",
            "Audio group",
            CheckStatus.WARNING,
            f"User '{username}' not in audio group",
            fix_available=True,
            fix_key="add_audio_group",
            logout_warning="Logout or restart required after being added to the audio group.",
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
        fix_available=True,
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


def _path_in_env(fragment: str) -> bool:
    """Return True if fragment appears in the current $PATH."""
    return fragment in os.environ.get("PATH", "")


def check_profile_paths() -> EnvironmentCheck:
    profile = Path.home() / ".profile"
    xsession = Path.home() / ".xsessionrc"

    def _file_has(path: Path, *fragments: str) -> bool:
        if not path.exists():
            return False
        content = path.read_text()
        return all(f in content for f in fragments)

    in_files_yabridge = _file_has(profile, ".local/share/yabridge") or _file_has(
        xsession, ".local/share/yabridge"
    )
    in_files_wine = _file_has(profile, "wine-staging") or _file_has(xsession, "wine-staging")
    in_files_winefsync = _file_has(profile, "WINEFSYNC") or _file_has(xsession, "WINEFSYNC")
    all_in_files = in_files_yabridge and in_files_wine and in_files_winefsync

    in_path_yabridge = _path_in_env(".local/share/yabridge")
    in_path_wine = _path_in_env("wine-staging")
    all_in_path = in_path_yabridge and in_path_wine

    if all_in_files and all_in_path:
        return EnvironmentCheck(
            "profile_paths", "PATH (yabridge/wine)", CheckStatus.OK, "~/.profile configured"
        )

    if all_in_files and not all_in_path:
        return EnvironmentCheck(
            "profile_paths",
            "PATH (yabridge/wine)",
            CheckStatus.WARNING,
            "Paths configured in ~/.profile / ~/.xsessionrc but not active in current session",
            logout_warning="Logout or restart required for PATH changes to take effect.",
        )

    missing = []
    if not in_files_yabridge:
        missing.append("yabridge path")
    if not in_files_wine:
        missing.append("wine-staging path")
    if not in_files_winefsync:
        missing.append("WINEFSYNC=1")
    return EnvironmentCheck(
        "profile_paths",
        "PATH (yabridge/wine)",
        CheckStatus.WARNING,
        f"~/.profile missing: {', '.join(missing)}",
        fix_available=True,
        fix_key="configure_profile",
    )


def run_environment_checks() -> list[EnvironmentCheck]:
    return [
        check_wine(),           # 1
        check_yabridge(),       # 2  (binary + ctl merged)
        check_profile_paths(),  # 3
        check_audio_group(),    # 4
        check_realtime_limits(), # 5
        check_wine_configured(), # 6  (needs logout first if 3/4 pending)
        check_vst_dirs(),        # 7
        check_yabridge_paths(),  # 8
        check_pipewire(),        # 9
        check_wireplumber(),     # 10
    ]
