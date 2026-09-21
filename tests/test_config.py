import os

import pytest

from yt_fetch import config


def test_load_config_creates_file_with_defaults(isolated_config):
    cfg = config.load_config()

    assert cfg["type"] == "mp3"
    assert cfg["quality"] == "192"
    assert os.path.exists(config.get_config_file())


def test_load_config_reads_existing_values(isolated_config):
    with open(config.get_config_file(), "w") as f:
        f.write("type=mp4\nquality=320\n")

    cfg = config.load_config()

    assert cfg["type"] == "mp4"
    assert cfg["quality"] == "320"


def test_load_config_fills_missing_keys_with_defaults(isolated_config):
    with open(config.get_config_file(), "w") as f:
        f.write("type=mp4\n")

    cfg = config.load_config()

    assert cfg["resolution"] == "1080"
    assert cfg["remove_sponsors"] == "true"


def test_load_config_repairs_invalid_values(isolated_config, capsys):
    with open(config.get_config_file(), "w") as f:
        f.write("type=mp4\nquality=9999\n")

    cfg = config.load_config()

    assert cfg["quality"] == "192"
    assert "Invalid value" in capsys.readouterr().out


def test_load_config_preserves_case_for_path_keys(isolated_config):
    with open(config.get_config_file(), "w") as f:
        f.write("output_dir=C:\\Users\\Someone\\Downloads\n")

    cfg = config.load_config()

    assert cfg["output_dir"] == "C:\\Users\\Someone\\Downloads"


def test_load_config_lowercases_non_path_values(isolated_config):
    with open(config.get_config_file(), "w") as f:
        f.write("type=MP4\n")

    cfg = config.load_config()

    assert cfg["type"] == "mp4"


def test_save_config_writes_key_value_pairs(isolated_config):
    config.save_config({"type": "mp4", "quality": "320"})

    with open(config.get_config_file()) as f:
        contents = f.read()

    assert "type=mp4" in contents
    assert "quality=320" in contents


def test_validate_and_update_rejects_invalid_value(isolated_config):
    cfg = config.load_config()

    success = config.validate_and_update(cfg, "type", "wav")

    assert success is False
    assert cfg["type"] != "wav"


def test_validate_and_update_accepts_and_persists_valid_value(isolated_config):
    cfg = config.load_config()

    success = config.validate_and_update(cfg, "type", "mp4")

    assert success is True
    assert cfg["type"] == "mp4"
    assert config.load_config()["type"] == "mp4"


@pytest.fixture
def fresh_base_dir(monkeypatch):
    monkeypatch.setitem(config._base_dir_cache, "value", None)


def test_base_dir_is_user_config_dir_not_install_dir(fresh_base_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(config.platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    base_dir = config.get_base_dir()

    assert base_dir == os.path.join(str(tmp_path), "yt-fetch")
    assert os.path.isdir(base_dir)


def test_base_dir_uses_appdata_on_windows(fresh_base_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(config.platform, "system", lambda: "Windows")
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert config.get_base_dir() == os.path.join(str(tmp_path), "yt-fetch")


def test_default_output_dir_is_in_user_downloads(isolated_config, tmp_path, monkeypatch):
    monkeypatch.setattr(config.os.path, "expanduser", lambda path: path.replace("~", str(tmp_path)))

    cfg = config.load_config()

    assert cfg["output_dir"] == os.path.join(str(tmp_path), "Downloads", "yt-fetch")
