import os
import re

from mutagen.flac import FLAC
from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus
from mutagen.wave import WAVE
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


def _uslt(lyrics, lang):
    return USLT(encoding=3, lang='eng' if lang.startswith('en') else 'XXX', desc='', text=lyrics)


def write_lyrics(path, lyrics, lang):
    """Writes lyrics into the tag each container's players read them from."""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.mp3':
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()
        tags.delall('USLT')
        tags.add(_uslt(lyrics, lang))
        tags.save(path, v2_version=3)
    elif ext == '.wav':
        audio = WAVE(path)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.delall('USLT')
        audio.tags.add(_uslt(lyrics, lang))
        audio.save(v2_version=3)
    elif ext == '.m4a':
        audio = MP4(path)
        audio['\xa9lyr'] = [lyrics]
        audio.save()
    elif ext in ('.flac', '.opus'):
        audio = FLAC(path) if ext == '.flac' else OggOpus(path)
        audio['LYRICS'] = [lyrics]
        audio.save()
    else:
        return False
    return True


class EmbedLyricsPP(PostProcessor):
    """Writes the downloaded subtitles into an audio file's lyrics tag, since
    ffmpeg can't embed subtitle tracks in audio-only formats."""

    def run(self, info):
        subtitles = info.get('requested_subtitles') or {}
        lang, subtitle = _pick_subtitle(subtitles)
        if subtitle is None:
            self.to_screen('No subtitles available to use as lyrics')
            return [], info

        with open(subtitle['filepath'], 'r', encoding='utf-8-sig') as f:
            lyrics = srt_to_lyrics(f.read())

        if lyrics and not write_lyrics(info['filepath'], lyrics, lang):
            self.to_screen(f"Can't embed lyrics in {os.path.basename(info['filepath'])}")

        #every downloaded subtitle file is left over once the lyrics are embedded
        leftovers = [sub['filepath'] for sub in subtitles.values()
                     if sub.get('filepath') and os.path.exists(sub['filepath'])]
        return leftovers, info
