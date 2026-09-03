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

try:
    from yabridge_gui._version import version as __version__
except ImportError:
    __version__ = "2.0.0"

__all__ = ["__version__"]
