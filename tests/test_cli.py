import argparse
import sys

import pytest

import cli


def _args(**overrides):
    defaults = {key: None for key in cli.OVERRIDABLE_KEYS}
    defaults.update(url=None, batch=None, output_dir=None)
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


def test_apply_overrides_handles_output_dir_separately():
    base_config = {"type": "mp3", "output_dir": "/old"}

    result = cli.apply_overrides(base_config, _args(output_dir="/new"))

    assert result["output_dir"] == "/new"


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
    monkeypatch.setattr(sys, "argv", ["yt-fetch", "--type", "wav"])

    with pytest.raises(SystemExit):
        cli.parse_args()
