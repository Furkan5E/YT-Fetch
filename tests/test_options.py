import pytest

from yt_fetch.downloader import options as options_module
from yt_fetch.downloader.options import build_ydl_opts


@pytest.fixture(autouse=True)
def _stub_ffmpeg(monkeypatch):
    """build_ydl_opts resolves an ffmpeg path as its first step; these tests
    are about option-building, not ffmpeg discovery, so stub it out."""
    monkeypatch.setattr(options_module, "get_ffmpeg_path", lambda config: "/fake/ffmpeg")


def _config(output_dir, **overrides):
    base = {
        "type": "mp3",
        "quality": 192,
        "resolution": 1080,
        "metadata": False,
        "allow_playlists": False,
        "remove_sponsors": False,
        "embed_lyrics": False,
        "output_dir": str(output_dir),
    }
    base.update(overrides)
    return base


def test_mp3_format_and_extract_audio_postprocessor(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, quality=320))

    assert opts["format"] == "bestaudio/best"
    assert {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "320",
    } in opts["postprocessors"]


def test_mp4_format_with_resolution_cap(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, type="mp4", resolution=720))

    assert opts["format"] == "bv*[height<=720]+ba/b[height<=720]"
    assert opts["merge_output_format"] == "mp4"


def test_mp4_format_with_best_resolution(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, type="mp4", resolution="best"))

    assert opts["format"] == "bv*+ba/b"


def test_mp4_format_prefers_resolution_then_compatible_codecs(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, type="mp4"))

    assert opts["format_sort"] == ["res", "fps", "vcodec:h264", "acodec:aac"]


def test_mp4_remuxes_single_file_fallback_to_mp4(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, type="mp4"))

    assert {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"} in opts["postprocessors"]


def test_metadata_true_adds_thumbnail_and_metadata_postprocessors(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, metadata=True))

    assert opts["writethumbnail"] is True
    assert {"key": "FFmpegMetadata"} in opts["postprocessors"]
    assert {"key": "EmbedThumbnail"} in opts["postprocessors"]


def test_metadata_false_skips_thumbnail(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, metadata=False))

    assert "writethumbnail" not in opts
    assert not any(pp["key"] == "FFmpegMetadata" for pp in opts["postprocessors"])


def test_remove_sponsors_adds_sponsorblock_postprocessors(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, remove_sponsors=True))

    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "SponsorBlock" in keys
    assert "ModifyChapters" in keys


def test_embed_lyrics_adds_subtitle_postprocessors(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, embed_lyrics=True))

    assert opts["writesubtitles"] is True
    assert opts["subtitleslangs"] == ["en", "orig"]
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegSubtitlesConvertor" in keys
    assert "FFmpegEmbedSubtitle" in keys


def test_allow_playlists_controls_noplaylist_flag(tmp_path):
    single_video = build_ydl_opts(_config(tmp_path, allow_playlists=False))
    full_playlist = build_ydl_opts(_config(tmp_path, allow_playlists=True))

    assert single_video["noplaylist"] is True
    assert full_playlist["noplaylist"] is False


def test_output_dir_is_created(tmp_path):
    out_dir = tmp_path / "downloads"

    build_ydl_opts(_config(out_dir))

    assert out_dir.is_dir()
