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
        )
    except KeyError:
        return EnvironmentCheck(
            "audio_group", "Audio group", CheckStatus.UNKNOWN, "audio group not found"
        )


def _read_proc_limits() -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        for line in Path("/proc/self/limits").read_text().splitlines():
            if line.startswith("Max realtime priority"):
                result["rtprio"] = line.split()[-1]
            elif line.startswith("Max nice priority"):
                result["nice"] = line.split()[-1]
            elif line.startswith("Max locked memory"):
                parts = line.split()
                result["memlock"] = parts[-2]
    except OSError:
        pass
    return result


def _limits_conf_has_audio_limits() -> bool:
    limits_file = Path("/etc/security/limits.conf")
    if not limits_file.exists():
        return False
    content = limits_file.read_text()
    return "@audio" in content and "rtprio" in content and "memlock" in content


def check_realtime_limits() -> EnvironmentCheck:
    proc = _read_proc_limits()
    rtprio_ok = int(proc.get("rtprio", "0") or "0") >= 95
    nice_ok = int(proc.get("nice", "0") or "0") >= 10
    memlock_ok = proc.get("memlock", "") == "unlimited"

    if rtprio_ok and nice_ok and memlock_ok:
        return EnvironmentCheck(
            "rt_limits", "Realtime limits", CheckStatus.OK, "rtprio + memlock + nice active"
        )

    problems = []
    if not rtprio_ok:
        problems.append(f"rtprio={proc.get('rtprio', '?')} (need ≥95)")
    if not nice_ok:
        problems.append(f"nice={proc.get('nice', '?')} (need ≥10)")
    if not memlock_ok:
        problems.append(f"memlock={proc.get('memlock', '?')} (need unlimited)")

    configured = _limits_conf_has_audio_limits()
    return EnvironmentCheck(
        "rt_limits",
        "Realtime limits",
        CheckStatus.WARNING,
        ", ".join(problems),
        fix_available=not configured,
        fix_key="" if configured else "configure_rt_limits",
        logout_warning="Restart required for realtime limit changes to take effect."
        if configured
        else "",
    )


def check_pipewire() -> EnvironmentCheck:
    ok, ver = _command_version("pipewire")
    if not ok:
        return EnvironmentCheck(
            "pipewire",
            "PipeWire",
            CheckStatus.MISSING,
            "pipewire not found",
            fix_available=True,
            fix_key="install_pipewire_jack",
        )
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
    return EnvironmentCheck(
        "wireplumber",
        "WirePlumber",
        CheckStatus.MISSING,
        "Not found",
        fix_available=True,
        fix_key="install_wireplumber",
    )


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
    local = Path.home() / ".local/share/yabridge/yabridgectl"
    ctl = str(local) if local.exists() else "yabridgectl"
    ok, out = _run([ctl, "list"])
    if ok:
        expected = [
            str(Path.home() / ".wine/drive_c/Program Files/Common Files/VST3"),
            str(Path.home() / ".wine/drive_c/Program Files/Steinberg/VstPlugins"),
            str(Path.home() / ".wine/drive_c/Program Files/VSTPlugins"),
        ]
        configured = [line.strip() for line in out.splitlines() if line.strip()]
        if all(d in configured for d in expected):
            return EnvironmentCheck(
                "yabridge_paths", "yabridge paths", CheckStatus.OK, "Paths configured"
            )
    return EnvironmentCheck(
        "yabridge_paths",
        "yabridge paths",
        CheckStatus.WARNING,
        "VST paths not configured in yabridgectl",
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
        check_wine(),  # 1
        check_yabridge(),  # 2  (binary + ctl merged)
        check_profile_paths(),  # 3
        check_audio_group(),  # 4
        check_realtime_limits(),  # 5
        check_wine_configured(),  # 6  (needs logout first if 3/4 pending)
        check_vst_dirs(),  # 7
        check_yabridge_paths(),  # 8
        check_pipewire(),  # 9
        check_wireplumber(),  # 10
    ]
