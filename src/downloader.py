import yt_dlp
import sys
import os
import platform
import shutil

class SilentLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def info(self, msg):      
        pass 
    def error(self, msg):
        print(f"\n[Error] {msg}")

def minimalist_progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        print(f"\r[ {percent} ] Downloading...       ", end='', flush=True)
    elif d['status'] == 'finished':
        print("\r[ 100% ] Processing media...     ", end='', flush=True)

def get_ffmpeg_path(config):
    """Locates ffmpeg via config override, local directory, or system PATH."""
    custom_path = config.get('ffmpeg_path', 'auto')
    
    #1 check if valid path in config
    if custom_path != 'auto':
        if os.path.exists(custom_path):
            return custom_path
        else:
            print(f"\n[Warning] Configured ffmpeg path '{custom_path}' not found.")
            print("          Falling back to auto-detection...")
    
    #2 check local directory
    local_path = './ffmpeg.exe' if platform.system() == 'Windows' else './ffmpeg'
    if os.path.exists(local_path):
        return local_path
    
    #3 check global system PATH
    system_path = shutil.which("ffmpeg")
    if system_path:
        return system_path
    
    #4 not found
    print("\n[Error] ffmpeg not found.")
    print("Please install it, place it in this folder, or set ffmpeg_path in config.txt.")
    sys.exit(1)

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

    #handle lyrics
    if config.get('embed_lyrics', 'false') == 'true':
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['en', 'orig'] 
        opts['postprocessors'].extend([
            {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'},
            {'key': 'FFmpegEmbedSubtitle'}
        ])

    #handle sponsor removal
    if config.get('remove_sponsors', 'true') == 'true':
        opts['postprocessors'].append({
            'key': 'SponsorBlock',
            'categories': ['sponsor', 'interaction', 'intro', 'outro']
        })

    #handle type
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

    #handle metadata
    if config['metadata'] == 'true':
        opts['writethumbnail'] = True
        opts['postprocessors'].append({'key': 'FFmpegMetadata'})
        opts['postprocessors'].append({'key': 'EmbedThumbnail'})

    return opts

def download_video(video_url, config):
    """Executes the download process."""
    ydl_opts = build_ydl_opts(config)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nFetching data for: {video_url}...")
            ydl.download([video_url])
            print("\nSuccessfully downloaded!")
            
    except yt_dlp.utils.DownloadError as e:
        print(f"\nError downloading the video: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")