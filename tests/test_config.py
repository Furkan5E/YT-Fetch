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


@pytest.mark.parametrize("quote", ['"', "'"])
def test_ffmpeg_path_strips_surrounding_quotes(quote):
    typed = f"{quote}C:\\Program Files\\ffmpeg\\ffmpeg.exe{quote}"

    assert config.parse_value("ffmpeg_path", typed) == "C:\\Program Files\\ffmpeg\\ffmpeg.exe"


def test_ffmpeg_path_expands_home(monkeypatch, tmp_path):
    monkeypatch.setattr(config.os.path, "expanduser", lambda path: path.replace("~", str(tmp_path)))

    assert config.parse_value("ffmpeg_path", "~/bin/ffmpeg") == f"{tmp_path}/bin/ffmpeg"


def test_ffmpeg_path_auto_in_any_case():
    assert config.parse_value("ffmpeg_path", "AUTO") == "auto"


def test_ffmpeg_path_that_does_not_exist_is_not_saved(isolated_config, tmp_path, capsys):
    cfg = config.load_config()

    assert config.validate_and_update(cfg, "ffmpeg_path", str(tmp_path / "nope" / "ffmpeg.exe")) is False

    assert "No ffmpeg found at" in capsys.readouterr().out
    assert config.load_config()["ffmpeg_path"] == "auto"


def test_ffmpeg_path_that_exists_is_saved(isolated_config, tmp_path):
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.write_text("")
    cfg = config.load_config()

    assert config.validate_and_update(cfg, "ffmpeg_path", str(ffmpeg)) is True
    assert config.validate_and_update(cfg, "ffmpeg_path", "auto") is True


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
    #only created once something is saved in it
    assert not os.path.exists(base_dir)


def test_config_folder_is_created_when_settings_are_saved(fresh_base_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(config.platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config.load_config()

    assert os.path.isfile(os.path.join(str(tmp_path), "yt-fetch", "config.toml"))


def test_base_dir_uses_appdata_on_windows(fresh_base_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(config.platform, "system", lambda: "Windows")
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert config.get_base_dir() == os.path.join(str(tmp_path), "yt-fetch")


def test_default_output_dir_is_in_user_downloads(isolated_config, tmp_path, monkeypatch):
    monkeypatch.delenv("YT_FETCH_OUTPUT_DIR", raising=False)
    monkeypatch.setattr(config.os.path, "expanduser", lambda path: path.replace("~", str(tmp_path)))

    cfg = config.load_config()

    assert cfg["output_dir"] == os.path.join(str(tmp_path), "Downloads", "yt-fetch")


def test_output_dir_env_var_is_not_saved_as_the_setting(isolated_config, tmp_path, monkeypatch):
    monkeypatch.setenv("YT_FETCH_OUTPUT_DIR", str(tmp_path / "mounted"))

    cfg = config.load_config()

    assert cfg["output_dir"] == config.get_default_output_dir()
    assert config.get_env_output_dir() == str(tmp_path / "mounted")


def test_output_dir_env_var_unset_or_empty_is_ignored(monkeypatch):
    assert config.get_env_output_dir() == ""
    monkeypatch.setenv("YT_FETCH_OUTPUT_DIR", "  ")
    assert config.get_env_output_dir() == ""


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


@pytest.mark.parametrize("text", ["²", "٣٢٠", "1²"])
def test_digits_int_cannot_read_are_left_as_text(text):
    assert config.parse_value("quality", text) == text


def test_non_ascii_digit_is_rejected_like_any_invalid_value(isolated_config, capsys):
    cfg = config.load_config()

    assert config.validate_and_update(cfg, "quality", config.parse_value("quality", "²")) is False
    assert "Invalid value for 'quality'" in capsys.readouterr().out


@pytest.mark.parametrize("text", ["", "   ", '""'])
def test_empty_output_dir_is_not_the_current_folder(text):
    assert config.parse_value("output_dir", text) == ""


def test_empty_output_dir_is_not_saved(isolated_config, capsys):
    cfg = config.load_config()
    before = cfg["output_dir"]

    assert config.validate_and_update(cfg, "output_dir", config.parse_value("output_dir", '""')) is False

    assert "'output_dir' needs a path." in capsys.readouterr().out
    assert config.load_config()["output_dir"] == before


@pytest.mark.parametrize("line", ['output_dir = ""', "output_dir = 5", "ffmpeg_path = true", 'ffmpeg_path = ""'])
def test_load_config_repairs_paths_that_are_empty_or_not_text(isolated_config, capsys, line):
    _write_config(line + "\n")
    key = line.split()[0]

    cfg = config.load_config()

    assert cfg[key] == config._default_config()[key]
    assert f"for '{key}' in config.toml" in capsys.readouterr().out


def test_unknown_keys_are_ignored_with_a_warning(isolated_config, capsys):
    _write_config('typ = "mp4"\n\n[extra]\nnote = 1\n')

    cfg = config.load_config()

    assert set(cfg) == set(config._default_config())
    out = capsys.readouterr().out
    assert "Unknown setting 'typ' in config.toml was ignored." in out
    assert "Unknown setting 'extra'" in out


def test_unknown_keys_stay_in_the_file_when_saving(isolated_config, capsys):
    _write_config('typ = "mp4"\n')
    cfg = config.load_config()

    config.validate_and_update(cfg, "quality", 320)

    with open(config.get_config_file(), encoding="utf-8") as f:
        assert 'typ = "mp4"' in f.read()


def test_key_in_another_case_is_updated_in_place(isolated_config):
    _write_config('Type = "mp4"\n')
    cfg = config.load_config()
    assert cfg["type"] == "mp4"

    config.validate_and_update(cfg, "type", "flac")

    with open(config.get_config_file(), encoding="utf-8") as f:
        text = f.read()
    assert 'Type = "flac"' in text
    assert "\ntype" not in text
    assert config.load_config()["type"] == "flac"


def _fail_to_write(monkeypatch):
    real_open = open

    def read_only(file, mode="r", *args, **kwargs):
        if "w" in mode:
            raise PermissionError(13, "Permission denied")
        return real_open(file, mode, *args, **kwargs)
    monkeypatch.setattr("builtins.open", read_only)


def test_setting_is_not_changed_when_it_cannot_be_saved(isolated_config, monkeypatch, capsys):
    cfg = config.load_config()
    _fail_to_write(monkeypatch)

    assert config.validate_and_update(cfg, "quality", 320) is False

    assert cfg["quality"] == 192
    assert "Couldn't save settings to" in capsys.readouterr().out


def test_reset_changes_nothing_when_it_cannot_be_saved(isolated_config, monkeypatch, capsys):
    cfg = config.load_config()
    config.validate_and_update(cfg, "quality", 320)
    _fail_to_write(monkeypatch)

    assert config.reset_config(cfg) == []

    assert cfg["quality"] == 320
    assert "Couldn't save settings to" in capsys.readouterr().out


def test_first_run_still_works_when_the_config_cannot_be_written(isolated_config, monkeypatch, capsys):
    _fail_to_write(monkeypatch)

    assert config.load_config() == config._default_config()
    assert "Couldn't save settings to" in capsys.readouterr().out


def test_file_broken_while_running_does_not_crash_a_save(isolated_config, capsys):
    cfg = config.load_config()
    _write_config("type = = broken\n")

    assert config.validate_and_update(cfg, "quality", 320) is False

    assert "Couldn't save settings to" in capsys.readouterr().out


def test_unreadable_config_exits_with_a_message(isolated_config, monkeypatch, capsys):
    config.load_config()

    def locked(config_file):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr(config, "_read_document", locked)

    with pytest.raises(SystemExit) as exit_info:
        config.load_config()

    assert exit_info.value.code == 1
    assert "Couldn't read" in capsys.readouterr().out
