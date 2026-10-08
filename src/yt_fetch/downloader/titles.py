from yt_dlp.postprocessor.common import PostProcessor


class DuplicateTitlePP(PostProcessor):
    """Files are named after the video's title, so two different videos with
    the same title in one download (playlists often have several "Intro"s)
    would be saved to the same file, the second replacing the first. Later
    ones get their video ID added to the name through the 'duplicate_suffix'
    field in the output template."""

    def __init__(self):
        super().__init__()
        self._first_id_by_title = {}

    def run(self, info):
        #casefold, since names differing only in case are one file on Windows and macOS
        title = (info.get('title') or '').casefold()
        first_id = self._first_id_by_title.setdefault(title, info.get('id'))
        if info.get('id') != first_id:
            info['duplicate_suffix'] = f" [{info['id']}]"
        return [], info
