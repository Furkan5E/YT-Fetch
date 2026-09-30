import os

import pytest

from yt_fetch import config


def _write_config(text):
    with open(config.get_config_file(), "w", encoding="utf-8") as f:
        f.write(text)


def test_load_config_creates_file_with_defaults(isolated_config):
    cfg = config.load_config()

    assert cfg["type"] == "mp3"
    assert cfg["quality"] == 192
    assert cfg["metadata"] is True
    assert os.path.exists(config.get_config_file())


def test_config_file_is_toml(isolated_config):
    assert config.get_config_file().endswith("config.toml")


def test_new_config_file_has_comments(isolated_config):
    config.load_config()

    with open(config.get_config_file(), encoding="utf-8") as f:
        contents = f.read()

    assert "# audio: mp3, m4a, opus, flac, wav" in contents
    assert "metadata = true" in contents


def test_load_config_reads_typed_values(isolated_config):
    _write_config('type = "mp4"\nquality = 320\nmetadata = false\n')

    cfg = config.load_config()

    assert cfg["type"] == "mp4"
    assert cfg["quality"] == 320
    assert cfg["metadata"] is False


def test_load_config_accepts_values_written_as_strings(isolated_config):
    _write_config('quality = "320"\nresolution = "720"\nmetadata = "false"\n')

    cfg = config.load_config()

    assert cfg["quality"] == 320
    assert cfg["resolution"] == 720
    assert cfg["metadata"] is False


def test_load_config_fills_missing_keys_with_defaults(isolated_config):
    _write_config('type = "mp4"\n')

    cfg = config.load_config()

    assert cfg["resolution"] == 1080
    assert cfg["remove_sponsors"] is True


def test_load_config_repairs_invalid_values(isolated_config, capsys):
    _write_config('type = "mp4"\nquality = 9999\n')

    cfg = config.load_config()

    assert cfg["quality"] == 192
    assert "Invalid value" in capsys.readouterr().out


def test_load_config_rejects_numbers_for_booleans(isolated_config):
    _write_config("metadata = 0\n")

    cfg = config.load_config()

    assert cfg["metadata"] is True


def test_load_config_exits_on_invalid_toml(isolated_config, capsys):
    _write_config("type = mp4\n")

    with pytest.raises(SystemExit):
        config.load_config()

    assert "not valid TOML" in capsys.readouterr().out


def test_load_config_preserves_case_for_path_keys(isolated_config, tmp_path):
    music = str(tmp_path / "My Music")
    _write_config(f"output_dir = '{music}'\n")

    cfg = config.load_config()

    assert cfg["output_dir"] == music


def test_load_config_lowercases_non_path_values(isolated_config):
    _write_config('type = "MP4"\n')

    cfg = config.load_config()

    assert cfg["type"] == "mp4"


def test_save_config_keeps_user_comments(isolated_config):
    _write_config('# my note\ntype = "mp3"  # keep me\n')

    config.save_config({"type": "mp4", "quality": 320})

    with open(config.get_config_file(), encoding="utf-8") as f:
        contents = f.read()

    assert "# my note" in contents
    assert 'type = "mp4"  # keep me' in contents
    assert "quality = 320" in contents


def test_save_config_writes_paths_without_escaped_backslashes(isolated_config, tmp_path):
    music = str(tmp_path / "Music")
    config.save_config({"output_dir": music})

    with open(config.get_config_file(), encoding="utf-8") as f:
        contents = f.read()

    #a literal string, so Windows backslashes are written as-is
    assert f"output_dir = '{music}'" in contents
    assert config.load_config()["output_dir"] == music


def test_parse_value_converts_cli_text():
    assert config.parse_value("metadata", "True") is True
    assert config.parse_value("quality", "320") == 320
    assert config.parse_value("resolution", "best") == "best"


def test_output_dir_expands_home(monkeypatch, tmp_path):
    monkeypatch.setattr(config.os.path, "expanduser", lambda path: path.replace("~", str(tmp_path)))

    assert config.parse_value("output_dir", "~/Music") == os.path.abspath(str(tmp_path) + "/Music")


def test_output_dir_expands_environment_variables(monkeypatch, tmp_path):
    monkeypatch.setenv("YT_FETCH_TEST_MUSIC", str(tmp_path))

    assert config.parse_value("output_dir", "$YT_FETCH_TEST_MUSIC") == str(tmp_path)


@pytest.mark.parametrize("quote", ['"', "'"])
def test_output_dir_strips_surrounding_quotes(tmp_path, quote):
    music = str(tmp_path / "My Music")

    assert config.parse_value("output_dir", f"  {quote}{music}{quote} ") == music


def test_output_dir_relative_paths_become_absolute(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    assert config.parse_value("output_dir", "Music") == str(tmp_path / "Music")


def test_ffmpeg_path_is_not_made_absolute():
    #"ffmpeg" on its own means "look on PATH", so it must stay as typed
    assert config.parse_value("ffmpeg_path", "ffmpeg") == "ffmpeg"


def test_validate_and_update_rejects_invalid_value(isolated_config):
    cfg = config.load_config()

    success = config.validate_and_update(cfg, "type", "avi")

    assert success is False
    assert cfg["type"] != "avi"


def test_validate_and_update_accepts_and_persists_valid_value(isolated_config):
    cfg = config.load_config()

    success = config.validate_and_update(cfg, "quality", 320)

    assert success is True
    assert cfg["quality"] == 320
    assert config.load_config()["quality"] == 320


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
    monkeypatch.delenv("YT_FETCH_OUTPUT_DIR", raising=False)
    monkeypatch.setattr(config.os.path, "expanduser", lambda path: path.replace("~", str(tmp_path)))

    cfg = config.load_config()

    assert cfg["output_dir"] == os.path.join(str(tmp_path), "Downloads", "yt-fetch")


def test_default_output_dir_env_var_takes_priority(isolated_config, tmp_path, monkeypatch):
    monkeypatch.setenv("YT_FETCH_OUTPUT_DIR", str(tmp_path / "mounted"))

    cfg = config.load_config()

    assert cfg["output_dir"] == str(tmp_path / "mounted")


def test_load_config_accepts_a_bom(isolated_config):
    with open(config.get_config_file(), "wb") as f:
        f.write('type = "mp4"\n'.encode("utf-8-sig"))

    assert config.load_config()["type"] == "mp4"


def test_load_config_reads_legacy_windows_encoding(isolated_config, monkeypatch):
    monkeypatch.setattr(config.locale, "getpreferredencoding", lambda do_setlocale=True: "cp1252")
    with open(config.get_config_file(), "wb") as f:
        f.write("output_dir = 'C:\\Müzik'\n".encode("cp1252"))

    assert config.load_config()["output_dir"] == config.normalise_path("C:\\Müzik")


def test_saving_rewrites_legacy_encoding_as_utf8(isolated_config, monkeypatch):
    monkeypatch.setattr(config.locale, "getpreferredencoding", lambda do_setlocale=True: "cp1252")
    with open(config.get_config_file(), "wb") as f:
        f.write("output_dir = 'C:\\Müzik'\n".encode("cp1252"))
    cfg = config.load_config()

    config.save_config(cfg)

    with open(config.get_config_file(), "rb") as f:
        assert "Müzik".encode("utf-8") in f.read()
