from yt_dlp.utils import remove_terminal_sequences


def clean_message(msg, prefix):
    """Strips yt-dlp's colour codes and its 'ERROR:'/'WARNING:' prefix."""
    return remove_terminal_sequences(str(msg)).strip().removeprefix(prefix).strip()

class QuietLogger:
    """A yt-dlp logger that hides yt-dlp's chatter but shows warnings, once
    each, since they explain things like missing formats. Errors are also
    raised as DownloadError, which download_video prints, so printing them
    here too would show each one twice."""
    def __init__(self):
        self._seen_warnings = set()

    def debug(self, msg):
        pass
    def info(self, msg):
        pass
    def warning(self, msg):
        msg = clean_message(msg, 'WARNING:')
        if msg in self._seen_warnings:
            return
        self._seen_warnings.add(msg)
        #starts on a new line so it doesn't run into the progress line
        print(f"\n[Warning] {msg}")
    def error(self, msg):
        pass

def minimalist_progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        print(f"\r[ {percent} ] Downloading...       ", end='', flush=True)
    elif d['status'] == 'finished':
        print("\r[ 100% ] Processing media...     ", end='', flush=True)
