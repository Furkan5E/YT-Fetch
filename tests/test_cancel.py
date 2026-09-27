import sys

import pytest

from yt_fetch import batch, main as main_module, repl
from yt_fetch.downloader import core


def _raise_interrupt(*args, **kwargs):
    raise KeyboardInterrupt


def test_download_video_reports_cancel_and_reraises(monkeypatch, capsys):
    monkeypatch.setattr(core, "_download", _raise_interrupt)

    with pytest.raises(KeyboardInterrupt):
        core.download_video("https://example.com/v", {})

    assert "Download cancelled." in capsys.readouterr().out


def test_batch_stops_at_cancel_and_reports_progress(tmp_path, monkeypatch, capsys):
    batch_file = tmp_path / "batch.txt"
    batch_file.write_text("link1\nlink2\nlink3\n")
    attempted = []

    def fake_download(link, config):
        attempted.append(link)
        if link == "link2":
            raise KeyboardInterrupt
        return True

    monkeypatch.setattr(batch.downloader, "download_video", fake_download)

    with pytest.raises(KeyboardInterrupt):
        batch.run_batch(str(batch_file), {})

    assert attempted == ["link1", "link2"]
    assert "Batch cancelled. 1/3 succeeded, 2 not downloaded." in capsys.readouterr().out


def test_repl_returns_to_prompt_after_cancelled_download(monkeypatch, capsys):
    inputs = iter(["https://example.com/v", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(repl.downloader, "download_video", _raise_interrupt)

    repl.run_repl({}, {})

    assert "Terminating application." in capsys.readouterr().out


def test_ctrl_c_at_the_prompt_still_exits(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", _raise_interrupt)

    repl.run_repl({}, {})

    assert "Exiting..." in capsys.readouterr().out


@pytest.mark.parametrize("argv", [
    ["yt-fetch", "https://example.com/v"],
    ["yt-fetch", "--batch", "links.txt"],
])
def test_non_interactive_cancel_exits_with_130(isolated_config, monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(main_module.downloader, "download_video", _raise_interrupt)
    monkeypatch.setattr(main_module, "run_batch", _raise_interrupt)

    with pytest.raises(SystemExit) as exit_info:
        main_module.main()

    assert exit_info.value.code == 130
