"""Unit tests for yabridge core helpers."""

from __future__ import annotations

from yabridge_gui.core.yabridge import (
    SyncResult,
    _parse_sync_output,
    get_vst_plugins,
)


def test_parse_sync_output_typical():
    output = "setting up 5 managed plugins\n2 new plugins, skipped 3 unrelated files"
    result = _parse_sync_output(output)
    assert result.setting_up == 5
    assert result.new_plugins == 2
    assert result.skipped == 3


def test_parse_sync_output_zeros():
    output = "setting up 0 managed plugins\n0 new plugins, skipped 0 unrelated files"
    result = _parse_sync_output(output)
    assert result.setting_up == 0
    assert result.new_plugins == 0
    assert result.skipped == 0


def test_parse_sync_output_partial():
    # Only some fields present — should default to 0
    result = _parse_sync_output("setting up 3 managed plugins")
    assert result.setting_up == 3
    assert result.new_plugins == 0
    assert result.skipped == 0


def test_get_vst_plugins_empty_dir(tmp_path):
    result = get_vst_plugins(tmp_path)
    assert result == []


def test_get_vst_plugins_missing_dir(tmp_path):
    result = get_vst_plugins(tmp_path / "nonexistent")
    assert result == []


def test_get_vst_plugins_finds_vst_files(tmp_path):
    (tmp_path / "Serum.vst3").mkdir()
    (tmp_path / "Massive.vst").touch()
    (tmp_path / "readme.txt").touch()
    result = get_vst_plugins(tmp_path)
    assert "Serum" in result
    assert "Massive" in result
    assert "readme" not in result


def test_sync_result_fields():
    r = SyncResult(setting_up=10, new_plugins=2, skipped=1, raw_output="test")
    assert r.setting_up == 10
    assert r.new_plugins == 2
    assert r.skipped == 1
