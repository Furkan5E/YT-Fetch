import argparse
import importlib.metadata
import sys

import pytest

import yt_fetch
from yt_fetch import cli


def _args(**overrides):
    defaults = {key: None for key in cli.OVERRIDABLE_KEYS}
    defaults.update(url=None, batch=None, output_dir=None, config_path=False)
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_apply_overrides_returns_unchanged_config_when_no_flags_set():
    base_config = {"type": "mp3", "quality": "192"}

    result = cli.apply_overrides(base_config, _args())

    assert result == base_config


def test_apply_overrides_merges_only_the_provided_flags():
    base_config = {"type": "mp3", "quality": "192", "resolution": "1080"}

    result = cli.apply_overrides(base_config, _args(type="mp4"))

    assert result["type"] == "mp4"
    assert result["quality"] == "192"
    assert base_config["type"] == "mp3"  #original config is not mutated


def test_apply_overrides_converts_flag_text_to_typed_values():
    base_config = {"quality": 192, "metadata": True}

    result = cli.apply_overrides(base_config, _args(quality="320", metadata="false"))

    assert result["quality"] == 320
    assert result["metadata"] is False


def test_apply_overrides_handles_output_dir_separately(tmp_path):
    base_config = {"type": "mp3", "output_dir": str(tmp_path / "old")}

    result = cli.apply_overrides(base_config, _args(output_dir=str(tmp_path / "new")))

    assert result["output_dir"] == str(tmp_path / "new")


def test_output_dir_flag_is_normalised(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = cli.apply_overrides({}, _args(output_dir='"Music"'))

    assert result["output_dir"] == str(tmp_path / "Music")


def test_parse_args_defaults_to_none_when_no_flags_given(monkeypatch, isolated_config):
    monkeypatch.setattr(sys, "argv", ["yt-fetch"])

    args = cli.parse_args()

    assert args.url is None
    assert args.type is None
    assert args.batch is None


def test_parse_args_reads_url_and_overrides(monkeypatch, isolated_config):
    monkeypatch.setattr(
        sys, "argv",
        ["yt-fetch", "https://example.com/v", "--type", "mp4", "--quality", "320"],
    )

    args = cli.parse_args()

    assert args.url == "https://example.com/v"
    assert args.type == "mp4"
    assert args.quality == "320"


def test_parse_args_rejects_invalid_choice(monkeypatch, isolated_config, capsys):
    monkeypatch.setattr(sys, "argv", ["yt-fetch", "--type", "avi"])

    with pytest.raises(SystemExit):
        cli.parse_args()


def test_version_flag_prints_installed_version(monkeypatch, isolated_config, capsys):
    monkeypatch.setattr(sys, "argv", ["yt-fetch", "--version"])

    with pytest.raises(SystemExit) as exit_info:
        cli.parse_args()

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"yt-fetch {yt_fetch.get_version()}"


def test_get_version_reads_package_metadata():
    assert yt_fetch.get_version() == importlib.metadata.version("yt-fetch")


def test_get_version_falls_back_when_not_installed(monkeypatch):
    def not_installed(name):
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(yt_fetch, "version", not_installed)

    assert yt_fetch.get_version() == "unknown"
