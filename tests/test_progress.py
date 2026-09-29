from yt_fetch.downloader.progress import QuietLogger, clean_message


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


def test_debug_info_and_errors_stay_quiet(capsys):
    logger = QuietLogger()

    logger.debug("[debug] Command-line config")
    logger.info("[youtube] Extracting URL")
    logger.error("ERROR: printed by download_video instead")

    assert capsys.readouterr().out == ""


def test_clean_message_strips_the_given_prefix():
    assert clean_message("ERROR: [youtube] abc: gone", "ERROR:") == "[youtube] abc: gone"
