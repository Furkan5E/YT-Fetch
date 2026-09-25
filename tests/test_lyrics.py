import subprocess

import pytest
from mutagen.id3 import ID3
from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise

from yt_fetch.downloader.lyrics import EmbedLyricsPP, srt_to_lyrics

SRT = """1
00:00:18,800 --> 00:00:21,800
[♪♪♪]

2
00:00:22,000 --> 00:00:24,000
<i>We're no strangers to love</i>

3
00:00:24,000 --> 00:00:26,000
We're no strangers to love

4
00:00:26,000 --> 00:00:28,000
♪ You know the rules ♪
(and so do I)

5
00:00:28,000 --> 00:00:30,000
[Music]
"""


def test_srt_to_lyrics_keeps_only_lyric_lines():
    assert srt_to_lyrics(SRT) == (
        "We're no strangers to love\n"
        "You know the rules\n"
        "(and so do I)"
    )


@pytest.fixture
def mp3_file(tmp_path):
    ffmpeg, _ = get_or_fetch_platform_executables_else_raise()
    path = tmp_path / "song.mp3"
    subprocess.run(
        [ffmpeg, "-loglevel", "error", "-f", "lavfi", "-i", "sine=d=1", "-q:a", "9", str(path)],
        check=True,
    )
    return path


def _subtitle(tmp_path, lang, text=SRT):
    path = tmp_path / f"song.{lang}.srt"
    path.write_text(text, encoding="utf-8")
    return {"filepath": str(path)}


def test_embeds_lyrics_as_uslt_and_returns_subtitles_for_deletion(tmp_path, mp3_file):
    subs = {"de": _subtitle(tmp_path, "de", "1\n00:00:01,000 --> 00:00:02,000\nHallo\n"),
            "en": _subtitle(tmp_path, "en")}
    info = {"filepath": str(mp3_file), "requested_subtitles": subs}

    to_delete, _ = EmbedLyricsPP().run(info)

    lyrics = ID3(mp3_file).getall("USLT")
    assert len(lyrics) == 1
    assert lyrics[0].lang == "eng"
    assert lyrics[0].text.startswith("We're no strangers to love")
    assert sorted(to_delete) == sorted(sub["filepath"] for sub in subs.values())


def test_falls_back_to_first_language_when_no_english(tmp_path, mp3_file):
    subs = {"de": _subtitle(tmp_path, "de", "1\n00:00:01,000 --> 00:00:02,000\nHallo\n")}
    info = {"filepath": str(mp3_file), "requested_subtitles": subs}

    EmbedLyricsPP().run(info)

    lyrics = ID3(mp3_file).getall("USLT")
    assert lyrics[0].text == "Hallo"
    assert lyrics[0].lang == "XXX"


def test_does_nothing_without_subtitles(mp3_file):
    info = {"filepath": str(mp3_file), "requested_subtitles": None}
    pp = EmbedLyricsPP()
    pp.to_screen = lambda *args, **kwargs: None

    to_delete, _ = pp.run(info)

    assert to_delete == []
    assert ID3(mp3_file).getall("USLT") == []
