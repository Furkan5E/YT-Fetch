import os
import shutil

import pytest
import yt_dlp

from yt_fetch.downloader import core


class _FakeYDL:
    """Stands in for yt_dlp.YoutubeDL. Downloading runs `action` (which can
    create files and call finish() like a completed video), then raises
    `error` if one is set."""
    error = None
    action = None
    #what extract_info returns for a url; anything else is a single video
    extracted = {}
    calls = []
    downloaded = []

    def __init__(self, opts):
        self.opts = opts
        self.post_hooks = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def add_post_processor(self, pp, when='post_process'):
        pass

    def add_post_hook(self, hook):
        self.post_hooks.append(hook)

    def finish(self, path):
        for hook in self.post_hooks:
            hook(str(path))

    def download(self, urls):
        _FakeYDL.calls.append("download")
        _FakeYDL.downloaded.extend(urls)
        #read from the class so the function isn't bound as a method
        if _FakeYDL.action:
            _FakeYDL.action(self)
        if self.error:
            raise self.error

    def extract_info(self, url, download=True, process=True, ie_key=None):
        _FakeYDL.calls.append(f"extract {url}")
        return _FakeYDL.extracted.get(url, {"id": "abc", "title": "Song"})

    def process_ie_result(self, info, download=True):
        self.download([info])


@pytest.fixture
def fake_ydl(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "build_ydl_opts", lambda config: {"paths": {"home": str(tmp_path)}})
    monkeypatch.setattr(core, "build_extra_postprocessors", lambda config: [])
    monkeypatch.setattr(core.yt_dlp, "YoutubeDL", _FakeYDL)
    yield _FakeYDL
    _FakeYDL.error = None
    _FakeYDL.action = None
    _FakeYDL.extracted = {}
    _FakeYDL.calls = []
    _FakeYDL.downloaded = []


def test_download_error_is_printed_once_without_prefix_or_colours(fake_ydl, capsys):
    fake_ydl.error = yt_dlp.utils.DownloadError(
        "\x1b[0;31mERROR:\x1b[0m [youtube] abc: This video is unavailable"
    )

    assert core.download_video("https://example.com/v", {"type": "mp3"}) is False

    out = capsys.readouterr().out
    assert out.count("This video is unavailable") == 1
    assert "[Error] [youtube] abc: This video is unavailable" in out
    assert "\x1b" not in out


def test_successful_download_returns_true(fake_ydl, capsys):
    assert core.download_video("https://example.com/v", {"type": "mp3"}) is True
    assert "Successfully downloaded!" in capsys.readouterr().out


def _temp_dir(ydl):
    return ydl.opts["paths"]["temp"]


def test_unfinished_files_get_their_own_folder_inside_the_output_dir(fake_ydl, tmp_path):
    seen = []
    fake_ydl.action = lambda ydl: seen.append(_temp_dir(ydl))

    core.download_video("https://example.com/v", {})

    assert os.path.dirname(seen[0]) == str(tmp_path)
    #and it's gone again once the download is over
    assert list(tmp_path.iterdir()) == []


def test_cancel_removes_partial_files(fake_ydl, tmp_path, capsys):
    def action(ydl):
        for name in ("song.webm.part", "song.webp"):
            with open(os.path.join(_temp_dir(ydl), name), "w") as f:
                f.write("partial")
    fake_ydl.action = action
    fake_ydl.error = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        core.download_video("https://example.com/v", {})

    assert list(tmp_path.iterdir()) == []
    assert "Removed 2 partial file(s)." in capsys.readouterr().out


def test_cancel_keeps_files_it_did_not_create(fake_ydl, tmp_path):
    (tmp_path / "old song.mp3").write_text("already here")

    def action(ydl):
        #e.g. a browser download or another yt-fetch finishing in the same folder
        (tmp_path / "someone elses file.zip").write_text("not ours")
    fake_ydl.action = action
    fake_ydl.error = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        core.download_video("https://example.com/v", {})

    assert sorted(p.name for p in tmp_path.iterdir()) == ["old song.mp3", "someone elses file.zip"]


def test_cancel_keeps_playlist_items_that_finished(fake_ydl, tmp_path):
    def action(ydl):
        finished = tmp_path / "first.mp3"
        finished.write_text("done")
        ydl.finish(finished)
        with open(os.path.join(_temp_dir(ydl), "second.webm.part"), "w") as f:
            f.write("partial")
    fake_ydl.action = action
    fake_ydl.error = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        core.download_video("https://example.com/list", {})

    assert sorted(p.name for p in tmp_path.iterdir()) == ["first.mp3"]


def test_failed_download_cleans_up_quietly(fake_ydl, tmp_path, capsys):
    def action(ydl):
        with open(os.path.join(_temp_dir(ydl), "song.webm.part"), "w") as f:
            f.write("partial")
    fake_ydl.action = action
    fake_ydl.error = yt_dlp.utils.DownloadError("ERROR: network dropped")

    assert core.download_video("https://example.com/v", {}) is False

    assert list(tmp_path.iterdir()) == []
    assert "partial file" not in capsys.readouterr().out


def test_temp_dir_removal_retries_while_a_file_is_locked(monkeypatch, tmp_path):
    temp_dir = tmp_path / ".yt-fetch-abc"
    temp_dir.mkdir()
    (temp_dir / "song.part").write_text("partial")
    real_rmtree = shutil.rmtree
    calls = []

    def locked_twice(path, **kwargs):
        calls.append(path)
        if len(calls) == 3:
            real_rmtree(path)
    monkeypatch.setattr(core.shutil, "rmtree", locked_twice)
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)

    core._remove_temp_dir(str(temp_dir), report=True)

    assert len(calls) == 3
    assert not temp_dir.exists()


def test_files_that_stay_locked_are_reported(monkeypatch, tmp_path, capsys):
    temp_dir = tmp_path / ".yt-fetch-abc"
    temp_dir.mkdir()
    (temp_dir / "song.temp.mp4").write_text("in use")
    monkeypatch.setattr(core.shutil, "rmtree", lambda path, **kwargs: None)
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)

    core._remove_temp_dir(str(temp_dir), report=True)

    out = capsys.readouterr().out
    assert "Couldn't remove:" in out
    assert "song.temp.mp4" in out
    assert "Removed" not in out


def test_prints_where_a_single_download_was_saved(fake_ydl, tmp_path, capsys):
    song = tmp_path / "Song Title.mp3"
    fake_ydl.action = lambda ydl: ydl.finish(song)

    assert core.download_video("https://example.com/v", {"output_dir": str(tmp_path)}) is True

    assert f"Saved to: {song}" in capsys.readouterr().out


def test_prints_folder_and_count_for_playlists(fake_ydl, tmp_path, capsys):
    def action(ydl):
        for name in ("one.mp3", "two.mp3", "three.mp3"):
            ydl.finish(tmp_path / name)
    fake_ydl.action = action

    core.download_video("https://example.com/list", {"output_dir": str(tmp_path)})

    assert f"Saved 3 files to: {tmp_path}" in capsys.readouterr().out


@pytest.mark.parametrize("text", [
    "https://www.youtube.com/watch?v=abc",
    "http://example.com/v",
    "youtu.be/abc",
    "www.youtube.com/watch?v=abc",
])
def test_links_are_recognised(text):
    assert core.looks_like_url(text) is True


@pytest.mark.parametrize("text", ["rick astley never gonna", "lofi", "daft punk - one more time"])
def test_search_terms_are_not_links(text):
    assert core.looks_like_url(text) is False


def test_search_terms_say_they_are_searching(fake_ydl, tmp_path, capsys):
    core.download_video("daft punk one more time", {"output_dir": str(tmp_path)})

    assert "Searching YouTube for: daft punk one more time" in capsys.readouterr().out


PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL123"


def test_playlist_links_are_refused_when_playlists_are_off(fake_ydl, capsys):
    fake_ydl.extracted = {PLAYLIST_URL: {"_type": "playlist", "title": "Road Trip"}}

    assert core.download_video(PLAYLIST_URL, {"allow_playlists": False}) is False

    out = capsys.readouterr().out
    assert 'That link is the playlist "Road Trip", and allow_playlists is off.' in out
    assert "download" not in fake_ydl.calls


def test_links_that_redirect_to_a_playlist_are_refused_too(fake_ydl, capsys):
    fake_ydl.extracted = {
        "https://example.com/channel": {"_type": "url", "url": PLAYLIST_URL},
        PLAYLIST_URL: {"_type": "playlist"},
    }

    assert core.download_video("https://example.com/channel", {}) is False

    assert "That link is a playlist" in capsys.readouterr().out
    assert "download" not in fake_ydl.calls


def test_playlist_links_download_when_playlists_are_on(fake_ydl):
    fake_ydl.extracted = {PLAYLIST_URL: {"_type": "playlist", "title": "Road Trip"}}

    assert core.download_video(PLAYLIST_URL, {"allow_playlists": True}) is True

    assert fake_ydl.calls == ["download"]


def test_single_videos_are_only_extracted_once(fake_ydl):
    assert core.download_video("https://example.com/v", {"allow_playlists": False}) is True

    assert fake_ydl.calls == ["extract https://example.com/v", "download"]


def test_searches_are_not_treated_as_playlists(fake_ydl):
    assert core.download_video("daft punk one more time", {"allow_playlists": False}) is True

    assert fake_ydl.calls == ["download"]


def test_errors_yt_dlp_raises_unwrapped_are_printed_as_errors(fake_ydl, capsys):
    fake_ydl.error = yt_dlp.utils.ExtractorError("Requested format is not available", expected=True)

    assert core.download_video("https://example.com/v", {}) is False

    assert "[Error] Requested format is not available" in capsys.readouterr().out


def test_links_without_a_scheme_are_opened_rather_than_searched(fake_ydl, capsys):
    assert core.download_video("youtu.be/abc", {}) is True

    assert fake_ydl.calls == ["extract https://youtu.be/abc", "download"]
    assert "Fetching data for: https://youtu.be/abc" in capsys.readouterr().out


def test_search_terms_with_a_colon_are_still_searched(fake_ydl):
    core.download_video("Eminem: Lose Yourself", {})

    #without the prefix yt-dlp reads "eminem:" as a URL scheme
    assert fake_ydl.downloaded == ["ytsearch1:Eminem: Lose Yourself"]
