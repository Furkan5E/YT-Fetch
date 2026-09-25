import os

from .ffmpeg import get_ffmpeg_path
from .progress import SilentLogger, minimalist_progress_hook


def _add_lyrics_opts(opts, config):
    if config.get('embed_lyrics', False):
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['en', 'orig']
        opts['postprocessors'].extend([
            {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'},
            {'key': 'FFmpegEmbedSubtitle'}
        ])

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

def _add_format_opts(opts, config):
    """Sets the target format (mp4 video or mp3 audio) and resolution."""
    if config['type'] == 'mp4':
        res = config.get('resolution', 1080)
        height = '' if res == 'best' else f'[height<={res}]'
        #any codec is allowed so high resolutions that YouTube only serves as
        #VP9/AV1 aren't skipped; at equal resolution h264/aac win for compatibility
        opts['format'] = f'bv*{height}+ba/b{height}'
        opts['format_sort'] = ['res', 'fps', 'vcodec:h264', 'acodec:aac']
        opts['merge_output_format'] = 'mp4'
        opts['postprocessors'].append({'key': 'FFmpegVideoRemuxer', 'preferedformat': 'mp4'})
    else:
        #default to mp3
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(config['quality']),
        })

def _add_metadata_opts(opts, config):
    if config['metadata']:
        opts['writethumbnail'] = True
        opts['postprocessors'].append({'key': 'FFmpegMetadata'})
        opts['postprocessors'].append({'key': 'EmbedThumbnail'})

def build_ydl_opts(config):
    """Dynamically builds yt-dlp options based on the current config."""
    ffmpeg_path = get_ffmpeg_path(config)

    #check if output directory exists
    out_dir = config.get('output_dir', os.path.join(os.getcwd(), 'downloads'))
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

    _add_lyrics_opts(opts, config)
    _add_sponsor_opts(opts, config)
    _add_format_opts(opts, config)
    _add_metadata_opts(opts, config)

    return opts
