from yt_dlp.postprocessor.sponsorblock import SponsorBlockPP
from yt_dlp.utils import PostProcessingError


class TolerantSponsorBlockPP(SponsorBlockPP):
    """SponsorBlock lookup that doesn't fail the download when the SponsorBlock
    API can't be reached; the segments are just left in."""

    @classmethod
    def pp_key(cls):
        #keeps "SponsorBlock" as the name in yt-dlp's messages
        return SponsorBlockPP.pp_key()

    def run(self, info):
        try:
            return super().run(info)
        except PostProcessingError as e:
            self.report_warning(f"Sponsor segments weren't removed: {e}")
            return [], info
