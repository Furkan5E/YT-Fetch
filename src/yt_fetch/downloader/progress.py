class SilentLogger:
    """A yt-dlp logger that suppresses everything. Errors are also raised as
    DownloadError, which download_video prints, so printing them here too
    would show each one twice."""
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def info(self, msg):
        pass
    def error(self, msg):
        pass

def minimalist_progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        print(f"\r[ {percent} ] Downloading...       ", end='', flush=True)
    elif d['status'] == 'finished':
        print("\r[ 100% ] Processing media...     ", end='', flush=True)
