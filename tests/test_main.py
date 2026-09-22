import os
import sys

import pytest

from yt_fetch import config
from yt_fetch.main import main


def test_config_path_prints_path_and_exits_without_loading(isolated_config, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["yt-fetch", "--config-path"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == config.get_config_file()
    assert not os.path.exists(config.get_config_file())
