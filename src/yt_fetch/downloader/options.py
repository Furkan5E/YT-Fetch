import os

from .ffmpeg import get_ffmpeg_path
from .progress import SilentLogger, minimalist_progress_hook


def _add_lyrics_opts(opts, config):
    if config.get('embed_lyrics', 'false') == 'true':
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['en', 'orig']
        opts['postprocessors'].extend([
            {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'},
            {'key': 'FFmpegEmbedSubtitle'}
        ])

def _add_sponsor_opts(opts, config):
    if config.get('remove_sponsors', 'true') == 'true':
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
        res = config.get('resolution', '1080')
        if res == 'best':
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            opts['format'] = f'bestvideo[ext=mp4][height<={res}]+bestaudio[ext=m4a]/best[ext=mp4][height<={res}]/best'
    else:
        #default to mp3
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': config['quality'],
        })

def _add_metadata_opts(opts, config):
    if config['metadata'] == 'true':
        opts['writethumbnail'] = True
        opts['postprocessors'].append({'key': 'FFmpegMetadata'})
        opts['postprocessors'].append({'key': 'EmbedThumbnail'})

def build_ydl_opts(config):
    """Dynamically builds yt-dlp options based on the current config."""
    ffmpeg_path = get_ffmpeg_path(config)
    allow_playlists = str(config.get('allow_playlists', 'false')).strip().lower()

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
        'noplaylist': allow_playlists == 'false',
        'postprocessors': []
    }

    _add_lyrics_opts(opts, config)
    _add_sponsor_opts(opts, config)
    _add_format_opts(opts, config)
    _add_metadata_opts(opts, config)

    return opts
