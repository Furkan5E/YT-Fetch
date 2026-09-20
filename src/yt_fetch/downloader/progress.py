class SilentLogger:
    """A yt-dlp logger that suppresses everything except errors."""
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
