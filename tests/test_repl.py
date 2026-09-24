from yt_fetch import config
from yt_fetch.repl import handle_config_command


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

    handle_config_command([".config", "type", "wav"], current_config, saved_config)

    assert current_config["type"] == "mp3"
    assert config.load_config()["type"] == "mp3"


def test_config_command_shows_config_file_path(isolated_config, capsys):
    saved_config = config.load_config()

    handle_config_command([".config"], dict(saved_config), saved_config)

    assert config.get_config_file() in capsys.readouterr().out
