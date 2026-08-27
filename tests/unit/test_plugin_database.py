"""Unit tests for the free plugin database."""

from __future__ import annotations

import pytest

from yabridge_gui.models.free_plugin import FreePlugin
from yabridge_gui.services.plugin_database import PluginDatabase


def test_free_plugin_from_dict():
    data = {
        "name": "Test Synth",
        "developer": "Test Dev",
        "description": "A test synth.",
        "category": "Synthesizer",
        "website": "https://example.com",
        "download": "https://example.com/download",
        "formats": ["VST3"],
        "platforms": ["Linux", "Windows"],
        "free": True,
    }
    plugin = FreePlugin.from_dict("test-synth", data)
    assert plugin.slug == "test-synth"
    assert plugin.name == "Test Synth"
    assert plugin.developer == "Test Dev"
    assert plugin.category == "Synthesizer"
    assert "VST3" in plugin.formats
    assert plugin.free is True


def test_free_plugin_defaults():
    plugin = FreePlugin.from_dict("minimal", {})
    assert plugin.slug == "minimal"
    assert plugin.name == "minimal"
    assert plugin.formats == []
    assert plugin.free is True


def test_plugin_database_loads_real_db():
    """Test that the real database directory loads without errors."""
    from pathlib import Path

    db_root = Path(__file__).parent.parent.parent / "database/plugins"
    if not db_root.exists():
        pytest.skip("database/plugins not found")
    db = PluginDatabase(db_root)
    plugins = db.load()
    assert len(plugins) > 0
    for p in plugins:
        assert p.name
        assert p.slug


def test_plugin_database_search(tmp_path):
    import yaml

    plugin_dir = tmp_path / "surge-xt"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.yaml").write_text(
        yaml.dump(
            {
                "name": "Surge XT",
                "developer": "Surge Synth Team",
                "category": "Synthesizer",
                "description": "Open-source synth.",
                "website": "https://surge-synthesizer.github.io/",
                "download": "https://github.com/surge-synthesizer/surge/releases",
                "formats": ["VST3"],
                "platforms": ["Linux"],
                "free": True,
            }
        )
    )
    db = PluginDatabase(tmp_path)
    results = db.search("surge")
    assert len(results) == 1
    assert results[0].name == "Surge XT"


def test_plugin_database_empty_dir(tmp_path):
    db = PluginDatabase(tmp_path)
    assert db.load() == []


def test_plugin_database_categories(tmp_path):
    import yaml

    for slug, cat in [("synth-a", "Synthesizer"), ("fx-b", "Effect")]:
        d = tmp_path / slug
        d.mkdir()
        (d / "plugin.yaml").write_text(yaml.dump({"name": slug, "category": cat}))
    db = PluginDatabase(tmp_path)
    cats = db.categories()
    assert "Synthesizer" in cats
    assert "Effect" in cats


def test_plugin_database_skips_invalid_yaml(tmp_path):
    bad = tmp_path / "bad-plugin"
    bad.mkdir()
    (bad / "plugin.yaml").write_text("{{invalid: yaml: [")
    db = PluginDatabase(tmp_path)
    assert db.load() == []
