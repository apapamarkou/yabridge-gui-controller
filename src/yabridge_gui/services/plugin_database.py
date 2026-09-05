"""Filesystem-based free plugin database."""

from __future__ import annotations

from pathlib import Path

import yaml

from yabridge_gui.models.free_plugin import FreePlugin

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


class PluginDatabase:
    def __init__(self, db_root: Path | None = None):
        if db_root is None:
            # Locate database/ relative to the package or project root
            here = Path(__file__).parent
            for candidate in [
                here.parent.parent.parent / "database/software",
                Path("/usr/share/yabridge-gui-controller/database/software"),
            ]:
                if candidate.exists():
                    db_root = candidate
                    break
        self._root = db_root
        self._cache: list[FreePlugin] | None = None

    def load(self) -> list[FreePlugin]:
        if self._cache is not None:
            return self._cache
        if self._root is None or not self._root.exists():
            return []
        plugins = []
        for entry in sorted(self._root.iterdir()):
            if not entry.is_dir():
                continue
            yaml_file = entry / "plugin.yaml"
            if not yaml_file.exists():
                continue
            try:
                data = yaml.safe_load(yaml_file.read_text())
                image = _find_image(entry)
                plugins.append(FreePlugin.from_dict(entry.name, data, image))
            except Exception:
                continue
        self._cache = plugins
        return plugins

    def search(self, query: str) -> list[FreePlugin]:
        q = query.lower()
        return [
            p
            for p in self.load()
            if q in p.name.lower() or q in p.developer.lower() or q in p.category.lower()
        ]

    def by_category(self, category: str) -> list[FreePlugin]:
        return [p for p in self.load() if p.category.lower() == category.lower()]

    def categories(self) -> list[str]:
        return sorted({p.category for p in self.load() if p.category})


def _find_image(directory: Path) -> Path | None:
    for ext in _IMAGE_EXTS:
        for name in ("image", "plugin", directory.name):
            p = directory / f"{name}{ext}"
            if p.exists():
                return p
    return None
