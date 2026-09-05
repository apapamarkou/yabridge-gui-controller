"""Unit tests for the audio app database."""

from __future__ import annotations

import pytest

from yabridge_gui.models.audio_app import AudioApp
from yabridge_gui.services.plugin_database import PluginDatabase


def test_audio_app_from_dict():
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
    app = AudioApp.from_dict("test-synth", data)
    assert app.slug == "test-synth"
    assert app.name == "Test Synth"
    assert app.developer == "Test Dev"
    assert app.category == "Synthesizer"
    assert "VST3" in app.formats
    assert app.free is True


def test_audio_app_defaults():
    app = AudioApp.from_dict("minimal", {})
    assert app.slug == "minimal"
    assert app.name == "minimal"
    assert app.formats == []
    assert app.free is True


def test_plugin_database_loads_real_db():
    """Test that the real database directory loads without errors."""
    from pathlib import Path

    db_root = Path(__file__).parent.parent.parent / "database/software"
    if not db_root.exists():
        pytest.skip("database/software not found")
    db = PluginDatabase(db_root)
    apps = db.load()
    assert len(apps) > 0
    for a in apps:
        assert a.name
        assert a.slug


def test_plugin_database_search(tmp_path):
    import yaml

    app_dir = tmp_path / "surge-xt"
    app_dir.mkdir()
    (app_dir / "info.yaml").write_text(
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
        (d / "info.yaml").write_text(yaml.dump({"name": slug, "category": cat}))
    db = PluginDatabase(tmp_path)
    cats = db.categories()
    assert "Synthesizer" in cats
    assert "Effect" in cats


def test_plugin_database_skips_invalid_yaml(tmp_path):
    bad = tmp_path / "bad-app"
    bad.mkdir()
    (bad / "info.yaml").write_text("{{invalid: yaml: [")
    db = PluginDatabase(tmp_path)
    assert db.load() == []
