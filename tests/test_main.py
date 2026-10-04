import io
import os
import sys

import pytest

from yt_fetch import config
from yt_fetch.main import _make_output_safe, main


def test_config_path_prints_path_and_exits_without_loading(isolated_config, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["yt-fetch", "--config-path"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == config.get_config_file()
    assert not os.path.exists(config.get_config_file())


def test_titles_the_output_encoding_cannot_hold_do_not_raise(monkeypatch):
    #what stdout looks like on Windows when it's redirected to a file or pipe
    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252"))

    _make_output_safe()
    print("Saved to: Şarkı \U0001f3b5.mp3")
    sys.stdout.flush()

    assert raw.getvalue().decode("cp1252").strip() == "Saved to: ?ark? ?.mp3"
