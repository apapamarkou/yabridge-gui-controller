"""Unit tests for environment checks."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from yabridge_gui.core.environment import (
    CheckStatus,
    check_audio_group,
    check_profile_paths,
    check_realtime_limits,
    check_vst_dirs,
)


def test_check_vst_dirs_all_present(tmp_path):
    fake_home = tmp_path
    (fake_home / ".wine/drive_c/Program Files/Steinberg/VstPlugins").mkdir(parents=True)
    (fake_home / ".wine/drive_c/Program Files/Common Files/VST3").mkdir(parents=True)
    (fake_home / ".wine/drive_c/Program Files/VSTPlugins").mkdir(parents=True)
    with patch.object(Path, "home", return_value=fake_home):
        result = check_vst_dirs()
    assert result.status == CheckStatus.OK


def test_check_vst_dirs_missing(tmp_path):
    with patch.object(Path, "home", return_value=tmp_path):
        result = check_vst_dirs()
    assert result.status == CheckStatus.WARNING


def test_check_realtime_limits_ok():
    proc_limits = (
        "Max realtime priority     95                   95                   \n"
        "Max nice priority         30                   30                   \n"
        "Max locked memory         unlimited            unlimited            bytes\n"
    )
    with patch("yabridge_gui.core.environment.Path") as mock_path:
        mock_path.return_value.read_text.return_value = proc_limits
        result = check_realtime_limits()
    assert result.status == CheckStatus.OK


def test_check_realtime_limits_missing_file():
    with patch("yabridge_gui.core.environment.Path") as mock_path:
        mock_path.return_value.read_text.side_effect = OSError
        mock_path.return_value.exists.return_value = False
        result = check_realtime_limits()
    assert result.status == CheckStatus.WARNING
    assert result.fix_key == "configure_rt_limits"


def test_check_profile_paths_ok(tmp_path):
    profile = tmp_path / ".profile"
    profile.write_text(
        'export PATH="$PATH:$HOME/.local/share/yabridge:$HOME/.local/share/wine-staging-9.21/bin"\n'
        "export WINEFSYNC=1\n"
    )
    fake_path = (
        "/usr/bin:"
        + str(tmp_path)
        + "/.local/share/yabridge:"
        + str(tmp_path)
        + "/.local/share/wine-staging-9.21/bin"
    )
    with (
        patch.object(Path, "home", return_value=tmp_path),
        patch.dict(os.environ, {"PATH": fake_path}),
    ):
        result = check_profile_paths()
    assert result.status == CheckStatus.OK


def test_check_profile_paths_missing(tmp_path):
    with patch.object(Path, "home", return_value=tmp_path):
        result = check_profile_paths()
    assert result.status == CheckStatus.WARNING


def test_check_audio_group_unknown_group():
    with patch("grp.getgrnam", side_effect=KeyError("audio")):
        result = check_audio_group()
    assert result.status == CheckStatus.UNKNOWN
