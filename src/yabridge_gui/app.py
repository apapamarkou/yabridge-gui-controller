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
