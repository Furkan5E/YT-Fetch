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
    """True for full URLs and scheme-less ones like youtu.be/abc."""
    return '://' in text or _BARE_URL.match(text) is not None

def _extract_unprocessed(ydl, url, max_redirects=5):
    """Extracts url without downloading it or expanding playlists, following
    the links some pages just redirect to."""
    info = ydl.extract_info(url, download=False, process=False) or {}
    for _ in range(max_redirects):
        if info.get('_type') != 'url':
            break
        info = ydl.extract_info(info['url'], download=False, process=False, ie_key=info.get('ie_key')) or {}
    return info

def _print_playlist_refused(info):
    title = info.get('title')
    name = f'the playlist "{title}"' if title else "a playlist"
    print(f"\n[Error] That link is {name}, and allow_playlists is off.")
    print("        Turn it on with `.config allow_playlists true` or `--allow-playlists true`.")

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
    if looks_like_url(video_url) and '://' not in video_url:
        #without a scheme yt-dlp would search for the link's text instead of opening it
        video_url = 'https://' + video_url
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for pp, when in build_extra_postprocessors(config):
                ydl.add_post_processor(pp, when=when)
            #called with the final file once a video is fully processed
            ydl.add_post_hook(lambda path: completed.append(os.path.abspath(path)))
            if not looks_like_url(video_url):
                print(f"\nSearching YouTube for: {video_url}...")
                ydl.download([video_url])
            elif config.get('allow_playlists', False):
                print(f"\nFetching data for: {video_url}...")
                ydl.download([video_url])
            else:
                print(f"\nFetching data for: {video_url}...")
                #'noplaylist' only covers video links that also name a playlist;
                #links to a playlist or channel itself have to be caught here
                info = _extract_unprocessed(ydl, video_url)
                if info.get('_type') == 'playlist':
                    _print_playlist_refused(info)
                    return False
                #carries on from the extraction above instead of repeating it
                ydl.process_ie_result(info, download=True)
            print("\nSuccessfully downloaded!")
            _print_saved(completed)
            return True

    #process_ie_result raises yt-dlp's other errors without wrapping them in DownloadError
    except yt_dlp.utils.YoutubeDLError as e:
        print(f"\n[Error] {clean_message(e, 'ERROR:')}")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return False
