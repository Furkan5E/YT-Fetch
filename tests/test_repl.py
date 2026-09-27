from yt_fetch import config
from yt_fetch.repl import COMMANDS, handle_config_command, run_repl


def test_config_update_does_not_persist_cli_overrides(isolated_config):
    saved_config = config.load_config()
    current_config = {**saved_config, "type": "mp4"}  #as if run with --type mp4

    handle_config_command([".config", "quality", "320"], current_config, saved_config)

    persisted = config.load_config()
    assert persisted["quality"] == 320
    assert persisted["type"] == "mp3"


def test_config_update_applies_to_current_session(isolated_config):
    saved_config = config.load_config()
    current_config = {**saved_config, "type": "mp4"}

    handle_config_command([".config", "quality", "320"], current_config, saved_config)

    assert current_config["quality"] == 320
    assert current_config["type"] == "mp4"


def test_invalid_config_update_changes_nothing(isolated_config):
    saved_config = config.load_config()
    current_config = dict(saved_config)

    handle_config_command([".config", "type", "avi"], current_config, saved_config)

    assert current_config["type"] == "mp3"
    assert config.load_config()["type"] == "mp3"


def test_config_command_shows_config_file_path(isolated_config, capsys):
    saved_config = config.load_config()

    handle_config_command([".config"], dict(saved_config), saved_config)

    assert config.get_config_file() in capsys.readouterr().out


def test_help_lists_every_command_and_setting(isolated_config, monkeypatch, capsys):
    inputs = iter(["help", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    saved_config = config.load_config()

    run_repl(dict(saved_config), saved_config)

    out = capsys.readouterr().out
    for command, _ in COMMANDS:
        assert command in out
    for key in saved_config:
        assert key in out
    assert config.get_batch_file() in out


def test_question_mark_is_an_alias_for_help(isolated_config, monkeypatch, capsys):
    inputs = iter(["?", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    download_calls = []
    monkeypatch.setattr("yt_fetch.repl.downloader.download_video", lambda *args: download_calls.append(args))

    run_repl({}, {})

    assert "Commands:" in capsys.readouterr().out
    assert download_calls == []


def test_every_setting_has_a_help_description():
    assert set(config.KEY_DESCRIPTIONS) == set(config._default_config())
