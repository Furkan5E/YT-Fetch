import pytest
import yt_dlp

from yt_fetch.downloader import core


class _FakeYDL:
    """Stands in for yt_dlp.YoutubeDL. download() runs `action` (which can
    create files and call finish() like a completed video), then raises
    `error` if one is set."""
    error = None
    action = None

    def __init__(self, opts):
        self.opts = opts
        self.post_hooks = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def add_post_processor(self, pp):
        pass

    def add_post_hook(self, hook):
        self.post_hooks.append(hook)

    def finish(self, path):
        for hook in self.post_hooks:
            hook(str(path))

    def download(self, urls):
        #read from the class so the function isn't bound as a method
        if _FakeYDL.action:
            _FakeYDL.action(self)
        if self.error:
            raise self.error


@pytest.fixture
def fake_ydl(monkeypatch):
    monkeypatch.setattr(core, "build_ydl_opts", lambda config: {"logger": None})
    monkeypatch.setattr(core, "build_extra_postprocessors", lambda config: [])
    monkeypatch.setattr(core.yt_dlp, "YoutubeDL", _FakeYDL)
    yield _FakeYDL
    _FakeYDL.error = None
    _FakeYDL.action = None


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


def test_cancel_removes_partial_files_but_keeps_existing_ones(fake_ydl, tmp_path, capsys):
    (tmp_path / "old song.mp3").write_text("already here")

    def action(ydl):
        (tmp_path / "song.webm.part").write_text("partial")
        (tmp_path / "song.webp").write_text("thumbnail")
    fake_ydl.action = action
    fake_ydl.error = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        core.download_video("https://example.com/v", {"output_dir": str(tmp_path)})

    assert sorted(p.name for p in tmp_path.iterdir()) == ["old song.mp3"]
    assert "Removed 2 partial file(s)." in capsys.readouterr().out


def test_cancel_keeps_playlist_items_that_finished(fake_ydl, tmp_path):
    def action(ydl):
        finished = tmp_path / "first.mp3"
        finished.write_text("done")
        ydl.finish(finished)
        (tmp_path / "second.webm.part").write_text("partial")
    fake_ydl.action = action
    fake_ydl.error = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        core.download_video("https://example.com/list", {"output_dir": str(tmp_path)})

    assert sorted(p.name for p in tmp_path.iterdir()) == ["first.mp3"]


def test_failed_download_does_not_delete_anything(fake_ydl, tmp_path):
    def action(ydl):
        (tmp_path / "song.webm.part").write_text("partial, can be resumed")
    fake_ydl.action = action
    fake_ydl.error = yt_dlp.utils.DownloadError("ERROR: network dropped")

    assert core.download_video("https://example.com/v", {"output_dir": str(tmp_path)}) is False
    assert (tmp_path / "song.webm.part").exists()


def test_remove_file_retries_while_file_is_locked(monkeypatch):
    calls = []

    def locked_twice(path):
        calls.append(path)
        if len(calls) < 3:
            raise PermissionError
    monkeypatch.setattr(core.os, "remove", locked_twice)
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)

    assert core._remove_file("song.part") is True
    assert len(calls) == 3


def test_files_that_stay_locked_are_reported(monkeypatch, tmp_path, capsys):
    locked = tmp_path / "song.temp.mp4"
    locked.write_text("in use")

    def always_locked(path):
        raise PermissionError
    monkeypatch.setattr(core.os, "remove", always_locked)
    monkeypatch.setattr(core.time, "sleep", lambda seconds: None)

    core._remove_partial_files(str(tmp_path), set(), set())

    out = capsys.readouterr().out
    assert "Couldn't remove:" in out
    assert "song.temp.mp4" in out


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
