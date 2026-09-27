import pytest
import yt_dlp

from yt_fetch.downloader import core


class _FakeYDL:
    """Stands in for yt_dlp.YoutubeDL; download() raises whatever it's given."""
    error = None

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def add_post_processor(self, pp):
        pass

    def download(self, urls):
        if self.error:
            raise self.error


@pytest.fixture
def fake_ydl(monkeypatch):
    monkeypatch.setattr(core, "build_ydl_opts", lambda config: {"logger": None})
    monkeypatch.setattr(core, "build_extra_postprocessors", lambda config: [])
    monkeypatch.setattr(core.yt_dlp, "YoutubeDL", _FakeYDL)
    yield _FakeYDL
    _FakeYDL.error = None


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
