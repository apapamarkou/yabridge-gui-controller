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

"""Free Plugins browser dialog."""

from __future__ import annotations

import subprocess

from PyQt6.QtCore import Qt
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

from yabridge_gui.models.free_plugin import FreePlugin
from yabridge_gui.services.plugin_database import PluginDatabase


class FreePluginsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Free Plugin Browser")
        self.setMinimumSize(800, 550)
        self._db = PluginDatabase()
        self._plugins: list[FreePlugin] = []
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

    def _populate(self, plugins: list[FreePlugin]) -> None:
        self._list.clear()
        self._filtered: list[FreePlugin] = plugins
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


class _PluginDetailWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._image = QLabel()
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setFixedHeight(120)
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

        self._plugin: FreePlugin | None = None

    def set_plugin(self, plugin: FreePlugin) -> None:
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
            pix = QPixmap(str(plugin.image_path)).scaledToHeight(
                110, Qt.TransformationMode.SmoothTransformation
            )
            self._image.setPixmap(pix)
        else:
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
        self._image.clear()

    def _open_website(self) -> None:
        if self._plugin and self._plugin.website:
            subprocess.Popen(["xdg-open", self._plugin.website])

    def _open_download(self) -> None:
        if self._plugin and self._plugin.download:
            subprocess.Popen(["xdg-open", self._plugin.download])
