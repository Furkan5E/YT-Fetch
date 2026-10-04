from yt_dlp.utils import remove_terminal_sequences


def clean_message(msg, prefix):
    """Strips yt-dlp's colour codes and its 'ERROR:'/'WARNING:' prefix."""
    return remove_terminal_sequences(str(msg)).strip().removeprefix(prefix).strip()

class QuietLogger:
    """A yt-dlp logger that hides yt-dlp's chatter but shows warnings and
    errors, once each. Errors are kept in `errors` so download_video can tell
    whether anything went wrong, since yt-dlp is set to carry on after them."""
    def __init__(self):
        self._seen_warnings = set()
        self.errors = []

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
        msg = clean_message(msg, 'ERROR:')
        if msg in self.errors:
            return
        self.errors.append(msg)
        print(f"\n[Error] {msg}")

def minimalist_progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        print(f"\r[ {percent} ] Downloading...       ", end='', flush=True)
    elif d['status'] == 'finished':
        print("\r[ 100% ] Processing media...     ", end='', flush=True)
