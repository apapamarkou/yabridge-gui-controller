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

"""Audio Apps browser dialog."""

from __future__ import annotations

import subprocess
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from yabridge_gui.models.audio_app import AudioApp
from yabridge_gui.services.plugin_database import PluginDatabase

_GITHUB_ZIP = "https://github.com/apapamarkou/yabridge-gui-controller/archive/refs/heads/main.zip"
_DB_PREFIX = "yabridge-gui-controller-main/database/software/"


class _UpdateWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, db_root: Path):
        super().__init__()
        self._db_root = db_root

    def run(self) -> None:
        try:
            with urllib.request.urlopen(_GITHUB_ZIP, timeout=30) as resp:
                data = resp.read()
            with zipfile.ZipFile(BytesIO(data)) as zf:
                entries = [
                    n for n in zf.namelist() if n.startswith(_DB_PREFIX) and n.endswith("info.yaml")
                ]
                if not entries:
                    self.finished.emit(False, "No info.yaml entries found in archive.")
                    return
                for name in entries:
                    rel = name[len(_DB_PREFIX) :]
                    dest = self._db_root / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(zf.read(name))
            self.finished.emit(True, f"Updated {len(entries)} entries.")
        except Exception as e:
            self.finished.emit(False, str(e))


class AudioAppsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audio Apps Browser")
        self.setMinimumSize(800, 550)
        self._db = PluginDatabase()
        self._plugins: list[AudioApp] = []
        self._init_ui()
        self._load()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)

        # Left: list + search/filter
        left = QVBoxLayout()
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search…")
        self._search.textChanged.connect(self._filter)
        self._category_combo = QComboBox()
        self._category_combo.addItem("All categories")
        self._category_combo.currentTextChanged.connect(self._filter)
        search_row.addWidget(self._search)
        search_row.addWidget(self._category_combo)
        left.addLayout(search_row)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._show_plugin)
        left.addWidget(self._list)

        self._update_btn = QPushButton("Update Apps List")
        self._update_btn.clicked.connect(self._update_db)
        left.addWidget(self._update_btn)

        layout.addLayout(left, 1)

        # Right: detail panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._detail = _PluginDetailWidget()
        scroll.setWidget(self._detail)
        layout.addWidget(scroll, 2)

    def _load(self) -> None:
        self._plugins = self._db.load()
        cats = self._db.categories()
        for cat in cats:
            self._category_combo.addItem(cat)
        self._populate(self._plugins)

    def _filter(self) -> None:
        query = self._search.text().strip()
        cat = self._category_combo.currentText()
        plugins = self._plugins
        if query:
            q = query.lower()
            plugins = [p for p in plugins if q in p.name.lower() or q in p.developer.lower()]
        if cat and cat != "All categories":
            plugins = [p for p in plugins if p.category == cat]
        self._populate(plugins)

    def _populate(self, plugins: list[AudioApp]) -> None:
        self._list.clear()
        self._filtered: list[AudioApp] = plugins
        for p in plugins:
            item = QListWidgetItem(f"{p.name}  [{p.category}]")
            self._list.addItem(item)
        if plugins:
            self._list.setCurrentRow(0)
        else:
            self._detail.clear()

    def _show_plugin(self, row: int) -> None:
        if 0 <= row < len(self._filtered):
            self._detail.set_plugin(self._filtered[row])

    def _update_db(self) -> None:
        if self._db._root is None:
            return
        self._update_btn.setEnabled(False)
        self._update_btn.setText("Updating…")
        self._worker = _UpdateWorker(self._db._root)
        self._worker.finished.connect(self._on_update_done)
        self._worker.start()

    def _on_update_done(self, ok: bool, msg: str) -> None:
        self._update_btn.setEnabled(True)
        self._update_btn.setText("Update Apps List")
        if ok:
            self._db._cache = None
            self._load()
        from PyQt6.QtWidgets import QMessageBox

        (QMessageBox.information if ok else QMessageBox.warning)(self, "Update", msg)


class _PluginDetailWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._image = QLabel()
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setFixedHeight(120)
        self._image.setCursor(Qt.CursorShape.PointingHandCursor)
        self._image.mousePressEvent = self._open_image_preview
        layout.addWidget(self._image)

        self._name = QLabel()
        self._name.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._name.setWordWrap(True)
        layout.addWidget(self._name)

        self._developer = QLabel()
        self._developer.setStyleSheet("color: gray;")
        layout.addWidget(self._developer)

        self._category = QLabel()
        layout.addWidget(self._category)

        self._description = QLabel()
        self._description.setWordWrap(True)
        self._description.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._description)

        self._formats = QLabel()
        layout.addWidget(self._formats)

        self._platforms = QLabel()
        layout.addWidget(self._platforms)

        btn_row = QHBoxLayout()
        self._website_btn = QPushButton("Website")
        self._website_btn.clicked.connect(self._open_website)
        self._download_btn = QPushButton("Download")
        self._download_btn.clicked.connect(self._open_download)
        btn_row.addWidget(self._website_btn)
        btn_row.addWidget(self._download_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._plugin: AudioApp | None = None
        self._image_path: Path | None = None

    def _open_image_preview(self, event=None) -> None:
        if not self._image_path or not self._image_path.exists():
            return
        from PyQt6.QtWidgets import QDialog, QScrollArea, QVBoxLayout

        dlg = QDialog(self)
        dlg.setWindowTitle(self._plugin.name if self._plugin else "Image Preview")
        layout = QVBoxLayout(dlg)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(str(self._image_path))
        lbl.setPixmap(pix)
        scroll.setWidget(lbl)
        layout.addWidget(scroll)
        dlg.resize(min(pix.width() + 40, 1200), min(pix.height() + 40, 800))
        dlg.exec()

    def set_plugin(self, plugin: AudioApp) -> None:
        self._plugin = plugin
        self._name.setText(plugin.name)
        self._developer.setText(f"by {plugin.developer}")
        self._category.setText(f"Category: {plugin.category}")
        self._description.setText(plugin.description)
        self._formats.setText(f"Formats: {', '.join(plugin.formats)}")
        self._platforms.setText(f"Platforms: {', '.join(plugin.platforms)}")
        self._website_btn.setEnabled(bool(plugin.website))
        self._download_btn.setEnabled(bool(plugin.download))

        if plugin.image_path and plugin.image_path.exists():
            self._image_path = plugin.image_path
            pix = QPixmap(str(plugin.image_path)).scaledToHeight(
                110, Qt.TransformationMode.SmoothTransformation
            )
            self._image.setPixmap(pix)
        else:
            self._image_path = None
            self._image.setText("(no image)")

    def clear(self) -> None:
        self._plugin = None
        for lbl in (
            self._name,
            self._developer,
            self._category,
            self._description,
            self._formats,
            self._platforms,
        ):
            lbl.clear()
        self._image_path = None
        self._image.clear()

    def _open_website(self) -> None:
        if self._plugin and self._plugin.website:
            subprocess.Popen(["xdg-open", self._plugin.website])

    def _open_download(self) -> None:
        if self._plugin and self._plugin.download:
            subprocess.Popen(["xdg-open", self._plugin.download])
