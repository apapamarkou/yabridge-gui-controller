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

from yabridge_gui.core.distro import Distribution, detect_distribution
from yabridge_gui.core.environment import CheckStatus, EnvironmentCheck, run_environment_checks
from yabridge_gui.core.system import get_architecture, get_kernel
from yabridge_gui.core.wine import get_wine_version
from yabridge_gui.core.yabridge import get_yabridge_version, get_yabridgectl_version, sync_plugins

__all__ = [
    "Distribution",
    "detect_distribution",
    "EnvironmentCheck",
    "CheckStatus",
    "run_environment_checks",
    "get_yabridge_version",
    "get_yabridgectl_version",
    "sync_plugins",
    "get_wine_version",
    "get_kernel",
    "get_architecture",
]
