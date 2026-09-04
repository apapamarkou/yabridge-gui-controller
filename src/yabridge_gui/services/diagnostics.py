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

"""System diagnostic report generation."""

from __future__ import annotations

import platform
from datetime import datetime

from yabridge_gui import __version__
from yabridge_gui.core.distro import detect_distribution
from yabridge_gui.core.environment import run_environment_checks
from yabridge_gui.core.wine import get_wine_version
from yabridge_gui.core.yabridge import (
    VST_DIRS,
    YABRIDGE_DIR,
    get_yabridge_version,
    get_yabridgectl_version,
)


def generate_diagnostic_report() -> str:
    distro = detect_distribution()
    checks = run_environment_checks()

    lines = [
        "=== Yabridge GUI Controller — Diagnostic Report ===",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Application version : {__version__}",
        f"Distribution        : {distro.name} {distro.version}",
        f"Distro ID           : {distro.id}",
        f"Family              : {distro.family}",
        f"Supported           : {'Yes' if distro.supported else 'No'}",
        f"Kernel              : {platform.release()}",
        f"Architecture        : {platform.machine()}",
        "",
        "--- Component Versions ---",
        f"Wine                : {get_wine_version() or 'Not found'}",
        f"yabridge            : {get_yabridge_version() or 'Not found'}",
        f"yabridgectl         : {get_yabridgectl_version() or 'Not found'}",
        "",
        "--- Environment Checks ---",
    ]

    for check in checks:
        icon = {"ok": "✓", "missing": "✗", "warning": "⚠", "unknown": "?", "unsupported": "—"}.get(
            check.status.value, "?"
        )
        lines.append(f"  {icon} {check.label:<25} {check.detail}")

    lines += [
        "",
        "--- Plugin Directories ---",
        f"yabridge dir        : {YABRIDGE_DIR}",
        f"  exists            : {YABRIDGE_DIR.exists()}",
    ]
    for d in VST_DIRS:
        lines.append(f"  {d}: {'exists' if d.exists() else 'missing'}")

    return "\n".join(lines)
