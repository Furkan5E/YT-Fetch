import os
import re
import shutil
import tempfile
import time

import yt_dlp

from .ffmpeg import FFmpegNotFoundError
from .options import build_ydl_opts, build_extra_postprocessors
from .progress import clean_message


_BARE_URL = re.compile(r'^[\w-]+(\.[\w-]+)+/')

def _remove_temp_dir(temp_dir, report, attempts=5):
    """Deletes the folder holding a download's unfinished files (.part files,
    temp files, thumbnails, subtitles, half-processed output). Nothing else in
    the output folder is touched."""
    count = sum(len(files) for _, _, files in os.walk(temp_dir))
    #on Windows an interrupted ffmpeg can hold a file open for a moment
    for attempt in range(attempts):
        shutil.rmtree(temp_dir, ignore_errors=True)
        if not os.path.exists(temp_dir):
            break
        if attempt < attempts - 1:
            time.sleep(0.5)
    leftovers = sorted(os.path.join(root, name) for root, _, files in os.walk(temp_dir) for name in files)
    removed = count - len(leftovers)
    if report and removed:
        print(f"Removed {removed} partial file(s).")
    if leftovers:
        print("Couldn't remove:")
        for path in leftovers:
            print(f"  - {path}")

def looks_like_url(text):
    """True for full URLs and scheme-less ones like youtu.be/abc, which
    yt-dlp also treats as links rather than search terms."""
    return '://' in text or _BARE_URL.match(text) is not None

def _print_saved(completed):
    if len(completed) == 1:
        print(f"Saved to: {completed[0]}")
    elif completed:
        #playlists can be long, so just point at the folder
        print(f"Saved {len(completed)} files to: {os.path.dirname(completed[0])}")

def download_video(video_url, config):
    """Executes the download process. Returns True on success, False on failure.
    Ctrl+C is reported and re-raised so callers can decide what it cancels."""
    try:
        ydl_opts = build_ydl_opts(config)
    except FFmpegNotFoundError as e:
        print(f"\n[Error] {e}")
        return False
    except Exception as e:
        print(f"\n[Error] Failed to prepare download options: {e}")
        return False

    #unfinished files get a folder of their own and are only moved into the
    #output folder once done, so cleaning up never deletes anyone else's files
    temp_dir = tempfile.mkdtemp(prefix='.yt-fetch-', dir=ydl_opts['paths']['home'])
    ydl_opts['paths']['temp'] = temp_dir
    cancelled = False
    try:
        return _download(video_url, config, ydl_opts)
    except KeyboardInterrupt:
        cancelled = True
        print("\nDownload cancelled.")
        raise
    finally:
        _remove_temp_dir(temp_dir, report=cancelled)

def _download(video_url, config, ydl_opts):
    #the final path of every video that fully finishes
    completed = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for pp, when in build_extra_postprocessors(config):
                ydl.add_post_processor(pp, when=when)
            #called with the final file once a video is fully processed
            ydl.add_post_hook(lambda path: completed.append(os.path.abspath(path)))
            if looks_like_url(video_url):
                print(f"\nFetching data for: {video_url}...")
            else:
                print(f"\nSearching YouTube for: {video_url}...")
            ydl.download([video_url])
            print("\nSuccessfully downloaded!")
            _print_saved(completed)
            return True

    except yt_dlp.utils.DownloadError as e:
        print(f"\n[Error] {clean_message(e, 'ERROR:')}")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return False
