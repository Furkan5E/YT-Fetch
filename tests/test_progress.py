import os

import pytest

from yt_fetch.downloader import progress
from yt_fetch.downloader.progress import QuietLogger, clean_message, progress_hook, progress_line


def test_warnings_are_shown_without_prefix_or_colours(capsys):
    QuietLogger().warning("\x1b[0;33mWARNING:\x1b[0m [youtube] Some formats may be missing")

    assert capsys.readouterr().out == "\n[Warning] [youtube] Some formats may be missing\n"


def test_repeated_warnings_are_shown_once(capsys):
    logger = QuietLogger()

    for _ in range(3):
        logger.warning("No supported JavaScript runtime could be found")
    logger.warning("Requested format is not available")

    out = capsys.readouterr().out
    assert out.count("JavaScript runtime") == 1
    assert out.count("[Warning]") == 2


def test_each_download_starts_with_no_warnings_seen(capsys):
    QuietLogger().warning("same warning")
    QuietLogger().warning("same warning")

    assert capsys.readouterr().out.count("[Warning]") == 2


def test_debug_and_info_stay_quiet(capsys):
    logger = QuietLogger()

    logger.debug("[debug] Command-line config")
    logger.info("[youtube] Extracting URL")

    assert capsys.readouterr().out == ""


def test_errors_are_shown_once_and_remembered(capsys):
    logger = QuietLogger()

    logger.error("\x1b[0;31mERROR:\x1b[0m [youtube] abc: Private video")
    logger.error("ERROR: [youtube] abc: Private video")

    assert capsys.readouterr().out == "\n[Error] [youtube] abc: Private video\n"
    assert logger.errors == ["[youtube] abc: Private video"]


def test_clean_message_strips_the_given_prefix():
    assert clean_message("ERROR: [youtube] abc: gone", "ERROR:") == "[youtube] abc: gone"


MB = 1024 * 1024


def _update(**fields):
    return {"status": "downloading", **fields}


def test_progress_shows_percent_size_speed_and_time_left():
    line = progress_line(_update(downloaded_bytes=3 * MB, total_bytes=12 * MB, speed=1.5 * MB, eta=6))

    assert line == "[ 25.0% ] 3.0 MB of 12.0 MB at 1.5 MB/s, 0:06 left"


def test_progress_uses_the_estimated_size_when_the_real_one_is_unknown():
    line = progress_line(_update(downloaded_bytes=1 * MB, total_bytes_estimate=4 * MB))

    assert line == "[ 25.0% ] 1.0 MB of 4.0 MB"


def test_progress_without_any_size_shows_what_has_arrived():
    #live streams and some sites never report a total
    line = progress_line(_update(downloaded_bytes=2 * MB, speed=None, eta=None))

    assert line == "[ ? ] 2.0 MB"


def test_progress_never_goes_past_100_percent():
    #an estimate can turn out smaller than the download
    line = progress_line(_update(downloaded_bytes=5 * MB, total_bytes_estimate=4 * MB))

    assert line.startswith("[ 100.0% ]")


def test_progress_shows_large_sizes_in_gb_and_long_waits_in_hours():
    line = progress_line(_update(downloaded_bytes=512 * MB, total_bytes=2048 * MB, speed=MB, eta=3725))

    assert line == "[ 25.0% ] 512.0 MB of 2.00 GB at 1.0 MB/s, 1:02:05 left"


def test_progress_counts_playlist_items():
    info = {"playlist_index": 3, "n_entries": 12}

    line = progress_line(_update(downloaded_bytes=MB, total_bytes=2 * MB, info_dict=info))

    assert line.startswith("[3/12] [ 50.0% ]")


@pytest.mark.parametrize("info", [{}, {"playlist_index": 1, "n_entries": 1}, {"playlist_index": None}])
def test_single_videos_have_no_counter(info):
    line = progress_line(_update(downloaded_bytes=MB, total_bytes=2 * MB, info_dict=info))

    assert line.startswith("[ 50.0% ]")


@pytest.fixture
def terminal(monkeypatch):
    """A terminal of a known width, with nothing on its progress line yet."""
    monkeypatch.setitem(progress._last_line, "length", 0)

    def set_width(columns):
        monkeypatch.setattr(progress.shutil, "get_terminal_size", lambda: os.terminal_size((columns, 24)))
    set_width(80)
    return set_width


def test_hook_rewrites_the_same_line(terminal, capsys):
    progress_hook(_update(downloaded_bytes=MB, total_bytes=2 * MB))

    out = capsys.readouterr().out
    assert out == "\r[ 50.0% ] 1.0 MB of 2.0 MB"


def test_hook_covers_what_was_left_of_a_longer_line(terminal, capsys):
    progress_hook(_update(downloaded_bytes=MB, total_bytes=2 * MB, speed=MB, eta=1))
    longer = len(capsys.readouterr().out)

    progress_hook({"status": "finished"})

    out = capsys.readouterr().out
    assert out.startswith("\r[ 100% ] Processing media...")
    assert len(out) == longer


def test_hook_cuts_the_line_to_the_terminal_width(terminal, capsys):
    terminal(20)

    progress_hook(_update(downloaded_bytes=MB, total_bytes=2 * MB, speed=MB, eta=1))

    #one short of the width, so the cursor doesn't wrap onto the next line
    assert len(capsys.readouterr().out) == len("\r") + 19


def test_processing_line_keeps_the_playlist_counter(terminal, capsys):
    progress_hook({"status": "finished", "info_dict": {"playlist_index": 2, "n_entries": 5}})

    assert capsys.readouterr().out == "\r[2/5] [ 100% ] Processing media..."
