"""Filesystem-based audio app database."""

from __future__ import annotations

from pathlib import Path

import yaml

from yabridge_gui.models.audio_app import AudioApp

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")

USER_DB_ROOT = Path.home() / ".local" / "share" / "yabridge-gui-controller" / "database"


class PluginDatabase:
    def __init__(self, db_root: Path | None = None):
        if db_root is None:
            here = Path(__file__).parent
            for candidate in [
                USER_DB_ROOT,  # user-updated database
                here.parent / "database",  # installed package
                Path("/usr/share/yabridge-gui-controller/database"),
            ]:
                if candidate.exists():
                    db_root = candidate
                    break
        self._root = db_root
        self._cache: list[AudioApp] | None = None

    def load(self) -> list[AudioApp]:
        if self._cache is not None:
            return self._cache
        if self._root is None or not self._root.exists():
            return []
        plugins: list[AudioApp] = []
        for entry in sorted(self._root.iterdir()):
            if not entry.is_dir():
                continue
            yaml_file = entry / "info.yaml"
            if not yaml_file.exists():
                continue
            try:
                data = yaml.safe_load(yaml_file.read_text())
                image = _find_image(entry)
                plugins.append(AudioApp.from_dict(entry.name, data, image))
            except Exception:
                continue
        self._cache = plugins
        return plugins

    def search(self, query: str) -> list[AudioApp]:
        q = query.lower()
        return [
            p
            for p in self.load()
            if q in p.name.lower()
            or q in p.developer.lower()
            or any(q in c.lower() for c in p.category)
        ]

    def by_category(self, category: str) -> list[AudioApp]:
        return [p for p in self.load() if category.lower() in (c.lower() for c in p.category)]

    def categories(self) -> list[str]:
        return sorted({c for p in self.load() for c in p.category if c})


def _find_image(directory: Path) -> Path | None:
    for ext in _IMAGE_EXTS:
        for name in ("image", "plugin", directory.name):
            p = directory / f"{name}{ext}"
            if p.exists():
                return p
    return None
