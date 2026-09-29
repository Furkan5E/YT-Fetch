import os
import time

import yt_dlp
from yt_dlp.utils import remove_terminal_sequences

from .ffmpeg import FFmpegNotFoundError
from .options import build_ydl_opts, build_extra_postprocessors, get_output_dir


def _clean_error(error):
    """Strips yt-dlp's colour codes and 'ERROR:' prefix from its messages."""
    return remove_terminal_sequences(str(error)).removeprefix('ERROR:').strip()

def _normalise(path):
    return os.path.normcase(os.path.abspath(path))

def _list_files(directory):
    if not os.path.isdir(directory):
        return set()
    return {_normalise(entry.path) for entry in os.scandir(directory) if entry.is_file()}

def _remove_file(path, attempts=5):
    #on Windows an interrupted ffmpeg can hold the file open for a moment
    for attempt in range(attempts):
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return True
        except PermissionError:
            if attempt < attempts - 1:
                time.sleep(0.5)
    return False

def _remove_partial_files(out_dir, files_before, completed):
    """Deletes files created by a cancelled download (.part files, temp files,
    thumbnails, subtitles, half-processed output), keeping files that were
    already there and any playlist items that fully finished."""
    partial = _list_files(out_dir) - files_before - {_normalise(path) for path in completed}
    leftovers = sorted(path for path in partial if not _remove_file(path))
    removed = len(partial) - len(leftovers)
    if removed:
        print(f"Removed {removed} partial file(s).")
    if leftovers:
        print("Couldn't remove:")
        for path in leftovers:
            print(f"  - {path}")

def _print_saved(completed):
    if len(completed) == 1:
        print(f"Saved to: {completed[0]}")
    elif completed:
        #playlists can be long, so just point at the folder
        print(f"Saved {len(completed)} files to: {os.path.dirname(completed[0])}")

def download_video(video_url, config):
    """Executes the download process. Returns True on success, False on failure.
    Ctrl+C is reported and re-raised so callers can decide what it cancels."""
    out_dir = get_output_dir(config)
    files_before = _list_files(out_dir)
    completed = []
    try:
        return _download(video_url, config, completed)
    except KeyboardInterrupt:
        print("\nDownload cancelled.")
        _remove_partial_files(out_dir, files_before, completed)
        raise

def _download(video_url, config, completed):
    """completed collects the final path of every video that fully finishes,
    so a cancelled playlist keeps the items it already downloaded."""
    try:
        ydl_opts = build_ydl_opts(config)
    except FFmpegNotFoundError as e:
        print(f"\n[Error] {e}")
        return False
    except Exception as e:
        print(f"\n[Error] Failed to prepare download options: {e}")
        return False

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for pp in build_extra_postprocessors(config):
                ydl.add_post_processor(pp)
            #called with the final file once a video is fully processed
            ydl.add_post_hook(lambda path: completed.append(os.path.abspath(path)))
            print(f"\nFetching data for: {video_url}...")
            ydl.download([video_url])
            print("\nSuccessfully downloaded!")
            _print_saved(completed)
            return True

    except yt_dlp.utils.DownloadError as e:
        print(f"\n[Error] {_clean_error(e)}")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return False
