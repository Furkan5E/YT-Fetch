import os
import re

from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from yt_dlp.postprocessor.common import PostProcessor

_TIMESTAMP = re.compile(r'-->')
_TAG = re.compile(r'<[^>]+>')
_SOUND_CUE = re.compile(r'\[[^\]]*\]')


def srt_to_lyrics(srt_text):
    """Strips cue numbers, timestamps and formatting tags from an .srt file,
    leaving one line of text per lyric line."""
    lines = []
    for line in srt_text.splitlines():
        line = _TAG.sub('', line).replace('♪', '').strip()
        if not line or line.isdigit() or _TIMESTAMP.search(line):
            continue
        #sound cues like "[Music]", or lines that were only music notes
        if _SOUND_CUE.fullmatch(line) or not any(c.isalnum() for c in line):
            continue
        #captions often repeat a line across consecutive cues
        if lines and lines[-1] == line:
            continue
        lines.append(line)
    return '\n'.join(lines)


def _pick_subtitle(subtitles):
    """Prefers an English track, otherwise the first one downloaded."""
    available = {lang: sub for lang, sub in subtitles.items()
                 if sub.get('filepath') and os.path.exists(sub['filepath'])}
    for lang in available:
        if lang.startswith('en'):
            return lang, available[lang]
    return next(iter(available.items()), (None, None))


class EmbedLyricsPP(PostProcessor):
    """Writes the downloaded subtitles into an mp3 as an ID3 lyrics (USLT)
    frame, since ffmpeg can't embed subtitle tracks in mp3."""

    def run(self, info):
        subtitles = info.get('requested_subtitles') or {}
        lang, subtitle = _pick_subtitle(subtitles)
        if subtitle is None:
            self.to_screen('No subtitles available to use as lyrics')
            return [], info

        with open(subtitle['filepath'], 'r', encoding='utf-8-sig') as f:
            lyrics = srt_to_lyrics(f.read())

        if lyrics:
            try:
                tags = ID3(info['filepath'])
            except ID3NoHeaderError:
                tags = ID3()
            tags.delall('USLT')
            tags.add(USLT(encoding=3, lang='eng' if lang.startswith('en') else 'XXX', desc='', text=lyrics))
            tags.save(info['filepath'], v2_version=3)

        #every downloaded subtitle file is left over once the lyrics are embedded
        leftovers = [sub['filepath'] for sub in subtitles.values()
                     if sub.get('filepath') and os.path.exists(sub['filepath'])]
        return leftovers, info
