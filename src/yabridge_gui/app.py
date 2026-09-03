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

import sys

from PyQt6.QtWidgets import QApplication

from yabridge_gui.gui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Yabridge GUI Controller")
    app.setOrganizationName("apapamarkou")
    window = MainWindow()
    window.show()
    return app.exec()
