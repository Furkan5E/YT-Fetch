import os

from .ffmpeg import get_ffmpeg_path
from .lyrics import EmbedLyricsPP
from .progress import SilentLogger, minimalist_progress_hook


#lossless formats have no bitrate, so 'quality' only applies to the others
AUDIO_TYPES = ['mp3', 'm4a', 'opus', 'flac', 'wav']
LOSSLESS_AUDIO_TYPES = ['flac', 'wav']
VIDEO_TYPES = ['mp4', 'mkv', 'webm']

#EmbedThumbnail fails outright on these instead of skipping
NO_THUMBNAIL_TYPES = ['wav', 'webm']

def _add_lyrics_opts(opts, config):
    """Downloads the video's subtitles to use as lyrics. Video formats get
    them as subtitle tracks; audio formats can't hold those, so EmbedLyricsPP
    (see build_extra_postprocessors) writes them into a lyrics tag instead."""
    if config.get('embed_lyrics', False):
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['all', '-live_chat']
        #webm only accepts WebVTT subtitle tracks
        sub_format = 'vtt' if config['type'] == 'webm' else 'srt'
        opts['postprocessors'].append({'key': 'FFmpegSubtitlesConvertor', 'format': sub_format})
        if config['type'] in VIDEO_TYPES:
            opts['postprocessors'].append({'key': 'FFmpegEmbedSubtitle'})

def _add_sponsor_opts(opts, config):
    if config.get('remove_sponsors', True):
        sponsor_categories = ['sponsor', 'interaction', 'intro', 'outro']
        #fetches and marks the segments as chapters
        opts['postprocessors'].append({
            'key': 'SponsorBlock',
            'categories': sponsor_categories,
            'when': 'after_filter'
        })
        opts['postprocessors'].append({
            'key': 'ModifyChapters',
            'remove_sponsor_segments': sponsor_categories,
            'force_keyframes': False
        })

def _add_video_format_opts(opts, config):
    res = config.get('resolution', 1080)
    height = '' if res == 'best' else f'[height<={res}]'
    video_type = config['type']

    if video_type == 'webm':
        #webm can only hold VP9/AV1 video and Opus/Vorbis audio, which YouTube serves as webm
        opts['format'] = f'bv*[ext=webm]{height}+ba[ext=webm]/b[ext=webm]{height}'
        opts['format_sort'] = ['res', 'fps']
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

    opts['merge_output_format'] = video_type

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
        'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        'ffmpeg_location': ffmpeg_path,
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'logger': SilentLogger(),
        'progress_hooks': [minimalist_progress_hook],
        'noplaylist': not config.get('allow_playlists', False),
        'postprocessors': []
    }

    #order matters: postprocessors run in the order they're added
    _add_sponsor_opts(opts, config)
    _add_format_opts(opts, config)
    _add_lyrics_opts(opts, config)
    _add_metadata_opts(opts, config)

    return opts

def build_extra_postprocessors(config):
    """Custom postprocessors, which yt-dlp only accepts via add_post_processor.
    They run after everything in opts['postprocessors']."""
    if config.get('embed_lyrics', False) and config['type'] in AUDIO_TYPES:
        return [EmbedLyricsPP()]
    return []
