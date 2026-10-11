import shutil

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

def format_duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"

def format_size(size):
    megabytes = size / (1024 * 1024)
    return f"{megabytes / 1024:.2f} GB" if megabytes >= 1024 else f"{megabytes:.1f} MB"

def _playlist_counter(d):
    """'[3/12] ' while downloading a playlist, otherwise nothing."""
    info = d.get('info_dict') or {}
    index = info.get('playlist_index')
    total = info.get('n_entries') or info.get('playlist_count')
    return f"[{index}/{total}] " if index and total and total > 1 else ''

def progress_line(d):
    """The text for one progress update, from whatever yt-dlp knows so far:
    the size, speed and time left are all missing at times."""
    downloaded = d.get('downloaded_bytes') or 0
    total = d.get('total_bytes') or d.get('total_bytes_estimate')
    if total:
        percent = min(downloaded / total * 100, 100)
        line = f"[ {percent:.1f}% ] {format_size(downloaded)} of {format_size(total)}"
    else:
        line = f"[ ? ] {format_size(downloaded)}"
    if d.get('speed'):
        line += f" at {format_size(d['speed'])}/s"
    if d.get('eta') is not None:
        line += f", {format_duration(d['eta'])} left"
    return _playlist_counter(d) + line

_last_line = {'length': 0}

def _print_line(text):
    """Rewrites the progress line in place. It's cut to the terminal's width,
    since a wrapped line can't be rewritten, and padded to cover a longer
    line that was there before."""
    text = text[:shutil.get_terminal_size().columns - 1]
    padding = ' ' * max(0, _last_line['length'] - len(text))
    _last_line['length'] = len(text)
    print(f"\r{text}{padding}", end='', flush=True)

def progress_hook(d):
    if d['status'] == 'downloading':
        _print_line(progress_line(d))
    elif d['status'] == 'finished':
        _print_line(f"{_playlist_counter(d)}[ 100% ] Processing media...")
