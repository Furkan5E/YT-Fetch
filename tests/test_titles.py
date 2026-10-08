import yt_dlp

from yt_fetch.downloader.titles import DuplicateTitlePP

OUTTMPL = "%(title)s%(duplicate_suffix|)s.%(ext)s"


def _filename(info):
    with yt_dlp.YoutubeDL({"outtmpl": OUTTMPL, "quiet": True}) as ydl:
        return ydl.prepare_filename({"ext": "mp3", **info})


def test_first_video_with_a_title_keeps_the_plain_name():
    _, info = DuplicateTitlePP().run({"id": "aaa", "title": "Intro"})

    assert _filename(info) == "Intro.mp3"


def test_another_video_with_the_same_title_gets_its_id_in_the_name():
    pp = DuplicateTitlePP()
    pp.run({"id": "aaa", "title": "Intro"})

    _, info = pp.run({"id": "bbb", "title": "Intro"})

    assert _filename(info) == "Intro [bbb].mp3"


def test_titles_differing_only_in_case_count_as_the_same():
    pp = DuplicateTitlePP()
    pp.run({"id": "aaa", "title": "Intro"})

    _, info = pp.run({"id": "bbb", "title": "INTRO"})

    assert _filename(info) == "INTRO [bbb].mp3"


def test_the_same_video_twice_is_not_a_duplicate():
    pp = DuplicateTitlePP()
    pp.run({"id": "aaa", "title": "Intro"})

    _, info = pp.run({"id": "aaa", "title": "Intro"})

    assert _filename(info) == "Intro.mp3"


def test_different_titles_are_left_alone():
    pp = DuplicateTitlePP()
    pp.run({"id": "aaa", "title": "Intro"})

    _, info = pp.run({"id": "bbb", "title": "Outro"})

    assert _filename(info) == "Outro.mp3"
