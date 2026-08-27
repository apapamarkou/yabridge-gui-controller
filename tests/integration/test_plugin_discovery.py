"""Integration tests for plugin discovery."""

from __future__ import annotations

from yabridge_gui.core.yabridge import get_vst_plugins


def test_vst_plugin_discovery_vst3(tmp_path):
    (tmp_path / "Serum.vst3").mkdir()
    (tmp_path / "Massive X.vst3").mkdir()
    plugins = get_vst_plugins(tmp_path)
    assert "Serum" in plugins
    assert "Massive X" in plugins


def test_vst_plugin_discovery_vst2(tmp_path):
    (tmp_path / "Sylenth1.vst").touch()
    plugins = get_vst_plugins(tmp_path)
    assert "Sylenth1" in plugins


def test_vst_plugin_discovery_ignores_non_vst(tmp_path):
    (tmp_path / "readme.txt").touch()
    (tmp_path / "config.json").touch()
    plugins = get_vst_plugins(tmp_path)
    assert plugins == []


def test_vst_plugin_discovery_sorted(tmp_path):
    for name in ["Zebra.vst3", "Absynth.vst3", "Massive.vst3"]:
        (tmp_path / name).mkdir()
    plugins = get_vst_plugins(tmp_path)
    assert plugins == sorted(plugins)


def test_vst_plugin_discovery_nonexistent_dir(tmp_path):
    plugins = get_vst_plugins(tmp_path / "does_not_exist")
    assert plugins == []
