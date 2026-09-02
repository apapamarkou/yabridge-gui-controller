"""Main application window — preserves original functionality."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from yabridge_gui import __version__
from yabridge_gui.core.environment import CheckStatus, run_environment_checks
from yabridge_gui.core.wine import get_wine_version
from yabridge_gui.core.yabridge import (
    SyncResult,
    get_vst_plugins,
    get_yabridgectl_version,
    sync_plugins,
)


class _SyncThread(QThread):
    sync_completed = pyqtSignal(object)  # SyncResult
    sync_failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            result = sync_plugins()
            self.sync_completed.emit(result)
        except Exception as exc:
            self.sync_failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Yabridge Controller")
        self._init_ui()
        self._check_environment()
        self._load_plugins()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        self.vst2_list = QListWidget()
        self.vst3_list = QListWidget()

        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self._scan_plugins)
        self.scan_button.setFixedHeight(40)
        font = self.scan_button.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        self.scan_button.setFont(font)

        self.setup_button = QPushButton("Setup Assistant")
        self.setup_button.clicked.connect(self._open_setup)

        free_plugins_button = QPushButton("Free Plugins")
        free_plugins_button.clicked.connect(self._open_free_plugins)

        about_button = QPushButton("About")
        about_button.clicked.connect(self._show_about)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        title = QLabel("<h2>Converted Plugins</h2><hr/>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        vst2_layout = QVBoxLayout()
        vst2_layout.addWidget(QLabel("VST2 Plugins"))
        vst2_layout.addWidget(self.vst2_list)
        vst3_layout = QVBoxLayout()
        vst3_layout.addWidget(QLabel("VST3 Plugins"))
        vst3_layout.addWidget(self.vst3_list)

        list_layout = QHBoxLayout()
        list_layout.addLayout(vst2_layout)
        list_layout.addLayout(vst3_layout)
        layout.addLayout(list_layout)

        # Scan row
        scan_layout = QHBoxLayout()
        scan_label = QLabel("Scan and convert new installed plugins")
        scan_layout.addWidget(scan_label)
        scan_layout.addStretch()
        scan_layout.addWidget(self.scan_button)
        layout.addLayout(scan_layout)

        # Bottom button row
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.setup_button)
        button_layout.addWidget(free_plugins_button)
        button_layout.addWidget(about_button)
        button_layout.addStretch()
        button_layout.addWidget(quit_button)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # ------------------------------------------------------------------
    # Environment checks (preserved from original)
    # ------------------------------------------------------------------

    def _check_environment(self) -> None:
        yabridgectl_ver = get_yabridgectl_version()
        wine_ver = get_wine_version()
        self.scan_button.setEnabled(bool(yabridgectl_ver) and bool(wine_ver))
        checks = run_environment_checks()
        all_ok = all(c.status == CheckStatus.OK for c in checks)
        self.setup_button.setStyleSheet("" if all_ok else "color: red; font-weight: bold;")

    # ------------------------------------------------------------------
    # Plugin loading (preserved from original)
    # ------------------------------------------------------------------

    def _load_plugins(self) -> None:
        vst2 = get_vst_plugins(Path.home() / ".vst/yabridge")
        self.vst2_list.clear()
        self.vst2_list.addItems(vst2)

        vst3 = get_vst_plugins(Path.home() / ".vst3/yabridge")
        self.vst3_list.clear()
        self.vst3_list.addItems(vst3)

    # ------------------------------------------------------------------
    # Scan (preserved from original, refactored to use core)
    # ------------------------------------------------------------------

    def _scan_plugins(self) -> None:
        self._progress_dialog = QDialog(self)
        self._progress_dialog.setWindowTitle("Scanning Plugins")

        layout = QVBoxLayout(self._progress_dialog)
        self._progress_label = QLabel("Scanning… Please wait.")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        layout.addWidget(self._progress_label)
        layout.addWidget(self._progress_bar)

        self._progress_value = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(50)

        self._sync_thread = _SyncThread()
        self._sync_thread.sync_completed.connect(self._handle_sync_completed)
        self._sync_thread.sync_failed.connect(self._handle_sync_failed)
        self._sync_thread.start()

        self._progress_dialog.exec()

    def _update_progress(self) -> None:
        self._progress_value = min(self._progress_value + 1, 99)
        self._progress_bar.setValue(self._progress_value)

    def _handle_sync_completed(self, result: SyncResult) -> None:
        self._timer.stop()
        self._progress_bar.setValue(100)
        self._progress_label.setText(
            f"<h2 style='text-align:center'>Scan completed!</h2>"
            f"<p>Scanned files: {result.setting_up}</p>"
            f"<p>New plugins: {result.new_plugins}</p>"
            f"<p>Skipped: {result.skipped}</p><hr/>"
        )
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.clicked.connect(self._progress_dialog.close)
        self._progress_dialog.layout().addWidget(btn)
        self._load_plugins()

    def _handle_sync_failed(self, error: str) -> None:
        self._timer.stop()
        QMessageBox.critical(self, "Sync Failed", f"yabridgectl sync failed:\n\n{error}")
        self._progress_dialog.close()

    # ------------------------------------------------------------------
    # Additional windows
    # ------------------------------------------------------------------

    def _open_setup(self) -> None:
        from yabridge_gui.gui.setup_dialog import SetupDialog

        dlg = SetupDialog(self)
        dlg.exec()

    def _open_free_plugins(self) -> None:
        from yabridge_gui.gui.free_plugins_dialog import FreePluginsDialog

        dlg = FreePluginsDialog(self)
        dlg.exec()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About",
            f"""<h1>Yabridge GUI Controller</h1>
<h2>Version {__version__}</h2>
<p>Facilitates the conversion of Windows VST2/VST3 plugins installed through wine-staging
using yabridge. This application <strong>does not manage plugin installation</strong>
or removal; those are handled by the plugin installers. It <strong>streamlines the
conversion</strong> process to Linux-native VST2/VST3 formats for seamless use with
your favorite DAW. Enjoy making music!</p>
<p>Created by: Andrianos Papamarkou</p>
<p><a href="https://github.com/apapamarkou/yabridge-gui-controller">Visit Yabridge GUI Controller on GitHub</a></p>
<p><a href="https://github.com/robbert-vdh/yabridge">Visit Yabridge on GitHub</a></p>
<p><a href="https://www.winehq.org/">Visit WineHQ on web</a></p>""",
        )
