import pytest

from downloader import options as options_module
from downloader.options import build_ydl_opts


@pytest.fixture(autouse=True)
def _stub_ffmpeg(monkeypatch):
    """build_ydl_opts resolves an ffmpeg path as its first step; these tests
    are about option-building, not ffmpeg discovery, so stub it out."""
    monkeypatch.setattr(options_module, "get_ffmpeg_path", lambda config: "/fake/ffmpeg")


def _config(output_dir, **overrides):
    base = {
        "type": "mp3",
        "quality": "192",
        "resolution": "1080",
        "metadata": "false",
        "allow_playlists": "false",
        "remove_sponsors": "false",
        "embed_lyrics": "false",
        "output_dir": str(output_dir),
    }
    base.update(overrides)
    return base


def test_mp3_format_and_extract_audio_postprocessor(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, quality="320"))

    assert opts["format"] == "bestaudio/best"
    assert {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "320",
    } in opts["postprocessors"]


def test_mp4_format_with_resolution_cap(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, type="mp4", resolution="720"))

    assert opts["format"] == (
        "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best"
    )


def test_mp4_format_with_best_resolution(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, type="mp4", resolution="best"))

    assert opts["format"] == "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"


def test_metadata_true_adds_thumbnail_and_metadata_postprocessors(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, metadata="true"))

    assert opts["writethumbnail"] is True
    assert {"key": "FFmpegMetadata"} in opts["postprocessors"]
    assert {"key": "EmbedThumbnail"} in opts["postprocessors"]


def test_metadata_false_skips_thumbnail(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, metadata="false"))

    assert "writethumbnail" not in opts
    assert not any(pp["key"] == "FFmpegMetadata" for pp in opts["postprocessors"])


def test_remove_sponsors_adds_sponsorblock_postprocessors(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, remove_sponsors="true"))

    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "SponsorBlock" in keys
    assert "ModifyChapters" in keys


def test_embed_lyrics_adds_subtitle_postprocessors(tmp_path):
    opts = build_ydl_opts(_config(tmp_path, embed_lyrics="true"))

    assert opts["writesubtitles"] is True
    assert opts["subtitleslangs"] == ["en", "orig"]
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegSubtitlesConvertor" in keys
    assert "FFmpegEmbedSubtitle" in keys


def test_allow_playlists_controls_noplaylist_flag(tmp_path):
    single_video = build_ydl_opts(_config(tmp_path, allow_playlists="false"))
    full_playlist = build_ydl_opts(_config(tmp_path, allow_playlists="true"))

    assert single_video["noplaylist"] is True
    assert full_playlist["noplaylist"] is False


def test_output_dir_is_created(tmp_path):
    out_dir = tmp_path / "downloads"

    build_ydl_opts(_config(out_dir))

    assert out_dir.is_dir()
