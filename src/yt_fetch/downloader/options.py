import os

from .ffmpeg import get_ffmpeg_path
from .lyrics import EmbedLyricsPP, PickLyricsTrackPP
from .progress import QuietLogger, progress_hook
from .sponsors import TolerantSponsorBlockPP
from .titles import DuplicateTitlePP


#lossless formats have no bitrate, so 'quality' only applies to the others
AUDIO_TYPES = ['mp3', 'm4a', 'opus', 'flac', 'wav']
LOSSLESS_AUDIO_TYPES = ['flac', 'wav']
VIDEO_TYPES = ['mp4', 'mkv', 'webm']

#EmbedThumbnail fails outright on these instead of skipping
NO_THUMBNAIL_TYPES = ['wav', 'webm']

SPONSOR_CATEGORIES = ['sponsor', 'interaction', 'intro', 'outro']

def _add_lyrics_opts(opts, config):
    """Downloads the video's subtitles to use as lyrics. Video formats get
    them all as subtitle tracks; audio formats can't hold those, so one track
    is picked and written into a lyrics tag instead (PickLyricsTrackPP and
    EmbedLyricsPP, see build_extra_postprocessors)."""
    if config.get('embed_lyrics', False):
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['all', '-live_chat']
        #webm only accepts WebVTT subtitle tracks
        sub_format = 'vtt' if config['type'] == 'webm' else 'srt'
        opts['postprocessors'].append({'key': 'FFmpegSubtitlesConvertor', 'format': sub_format})
        if config['type'] in VIDEO_TYPES:
            opts['postprocessors'].append({'key': 'FFmpegEmbedSubtitle'})

def _add_sponsor_opts(opts, config):
    """Cuts the segments that TolerantSponsorBlockPP (see
    build_extra_postprocessors) fetches and marks as chapters."""
    if config.get('remove_sponsors', True):
        opts['postprocessors'].append({
            'key': 'ModifyChapters',
            'remove_sponsor_segments': SPONSOR_CATEGORIES,
            'force_keyframes': False
        })

def _add_video_format_opts(opts, config):
    res = config.get('resolution', 1080)
    height = '' if res == 'best' else f'[height<={res}]'
    video_type = config['type']

    if video_type == 'webm':
        #webm can only hold VP9/AV1 video and Opus/Vorbis audio, which YouTube serves as webm
        opts['format'] = f'bv*[ext=webm]{height}+ba[ext=webm]/b[ext=webm]{height}/bv*{height}+ba/b{height}'
        opts['format_sort'] = ['res', 'fps']
        #only does anything when the fallback after the last '/' was needed: a
        #video with no webm streams is re-encoded, which is slow but works
        opts['postprocessors'].append({'key': 'FFmpegVideoConvertor', 'preferedformat': 'webm'})
    else:
        #any codec is allowed so high resolutions that YouTube only serves as
        #VP9/AV1 aren't skipped
        opts['format'] = f'bv*{height}+ba/b{height}'
        if video_type == 'mp4':
            #at equal resolution h264/aac win for compatibility
            opts['format_sort'] = ['res', 'fps', 'vcodec:h264', 'acodec:aac']
        else:
            #mkv holds any codec, so just take the best quality
            opts['format_sort'] = ['res', 'fps']
        opts['postprocessors'].append({'key': 'FFmpegVideoRemuxer', 'preferedformat': video_type})

    #webm falls back to mkv for streams it can't hold, which are then converted
    opts['merge_output_format'] = 'webm/mkv' if video_type == 'webm' else video_type

def _add_audio_format_opts(opts, config):
    audio_type = config['type']
    extract = {'key': 'FFmpegExtractAudio', 'preferredcodec': audio_type}
    if audio_type not in LOSSLESS_AUDIO_TYPES:
        extract['preferredquality'] = str(config['quality'])
    opts['format'] = 'bestaudio/best'
    opts['postprocessors'].append(extract)

def _add_format_opts(opts, config):
    """Sets the target format and, for video, the resolution."""
    if config['type'] in VIDEO_TYPES:
        _add_video_format_opts(opts, config)
    else:
        _add_audio_format_opts(opts, config)

def _add_metadata_opts(opts, config):
    if config['metadata']:
        opts['postprocessors'].append({'key': 'FFmpegMetadata'})
        if config['type'] not in NO_THUMBNAIL_TYPES:
            opts['writethumbnail'] = True
            opts['postprocessors'].append({'key': 'EmbedThumbnail'})

def _retry_delay(n):
    """Seconds to wait before one of yt-dlp's retries: 1, 2, 4... up to 20.
    yt-dlp passes n by name, counting from 0."""
    return min(2 ** n, 20)

def get_output_dir(config):
    return config.get('output_dir', os.path.join(os.getcwd(), 'downloads'))

def build_ydl_opts(config):
    """Dynamically builds yt-dlp options based on the current config."""
    ffmpeg_path = get_ffmpeg_path(config)

    #check if output directory exists
    out_dir = get_output_dir(config)
    os.makedirs(out_dir, exist_ok=True)

    #base options
    opts = {
        #duplicate_suffix is empty unless DuplicateTitlePP sets it
        'outtmpl': '%(title)s%(duplicate_suffix|)s.%(ext)s',
        #download_video adds a 'temp' folder that unfinished files are kept in
        'paths': {'home': out_dir},
        'ffmpeg_location': ffmpeg_path,
        'quiet': True,
        'no_warnings': False,
        'noprogress': True,
        'logger': QuietLogger(),
        'progress_hooks': [progress_hook],
        'noplaylist': not config.get('allow_playlists', False),
        #yt-dlp's own retries, for connections that drop partway through; a
        #download that still fails is tried again as a whole by download_video
        'retries': 10,
        'fragment_retries': 10,
        'retry_sleep_functions': {'http': _retry_delay, 'fragment': _retry_delay},
        #one video that can't be downloaded doesn't stop the rest of a playlist;
        #errors go to the logger instead of being raised. Not True, which would
        #also run a video's remaining processing steps after one of them failed
        'ignoreerrors': 'only_download',
        #anything that isn't a URL is searched on YouTube and the top result downloaded
        'default_search': 'ytsearch',
        'postprocessors': []
    }

    #order matters: postprocessors run in the order they're added
    _add_sponsor_opts(opts, config)
    _add_format_opts(opts, config)
    _add_lyrics_opts(opts, config)
    _add_metadata_opts(opts, config)

    return opts

def build_extra_postprocessors(config):
    """Custom postprocessors, which yt-dlp only accepts via add_post_processor,
    as (postprocessor, when) pairs. Those in the same stage as
    opts['postprocessors'] run after them."""
    extra = [(DuplicateTitlePP(), 'after_filter')]
    if config.get('remove_sponsors', True):
        extra.append((TolerantSponsorBlockPP(None, categories=SPONSOR_CATEGORIES), 'after_filter'))
    if config.get('embed_lyrics', False) and config['type'] in AUDIO_TYPES:
        extra.append((PickLyricsTrackPP(), 'after_filter'))
        extra.append((EmbedLyricsPP(), 'post_process'))
    return extra
