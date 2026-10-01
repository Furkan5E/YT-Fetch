from yt_dlp.postprocessor.sponsorblock import SponsorBlockPP
from yt_dlp.utils import PostProcessingError

from yt_fetch.downloader.sponsors import TolerantSponsorBlockPP


def test_unreachable_sponsorblock_does_not_fail_the_download(monkeypatch):
    def unreachable(self, info):
        raise PostProcessingError("Unable to communicate with SponsorBlock API")
    monkeypatch.setattr(SponsorBlockPP, "run", unreachable)
    pp = TolerantSponsorBlockPP(None)
    warnings = []
    monkeypatch.setattr(pp, "report_warning", warnings.append)
    info = {"id": "abc"}

    assert pp.run(info) == ([], info)
    assert "Unable to communicate with SponsorBlock API" in warnings[0]


def test_found_segments_are_passed_through(monkeypatch):
    def found(self, info):
        return [], {**info, "sponsorblock_chapters": ["segment"]}
    monkeypatch.setattr(SponsorBlockPP, "run", found)

    _, info = TolerantSponsorBlockPP(None).run({"id": "abc"})

    assert info["sponsorblock_chapters"] == ["segment"]
