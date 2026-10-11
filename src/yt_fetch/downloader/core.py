import os
import re
import shutil
import tempfile
import time

import yt_dlp

from .ffmpeg import FFmpegNotFoundError
from .options import build_ydl_opts, build_extra_postprocessors
from .progress import format_duration


_BARE_URL = re.compile(r'^[\w-]+(\.[\w-]+)+/')

#a download that fails with one of these is worth trying again from the
#start: fresh links from YouTube usually get past a 403, and the rest pass
#with time. Errors like "Video unavailable" would only fail the same way
MAX_ATTEMPTS = 3
RETRY_DELAY = 3
TRANSIENT_ERRORS = (
    'http error 403', 'http error 5', 'timed out', 'timeout', 'connection',
    'temporary failure', 'getaddrinfo', 'incompleteread', 'unable to download video data',
)
#returned by an attempt that failed in a way worth retrying
_RETRY = object()

def _is_transient(errors):
    return any(marker in error.lower() for error in errors for marker in TRANSIENT_ERRORS)

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

def _describe(result):
    """A search result as 'Title (3:45) by Channel', with whatever is known."""
    text = result.get('title') or result.get('url') or 'Unknown video'
    if result.get('duration'):
        text += f" ({format_duration(result['duration'])})"
    channel = result.get('channel') or result.get('uploader')
    if channel:
        text += f" by {channel}"
    return text

def _print_saved(completed):
    if len(completed) == 1:
        print(f"Saved to: {completed[0]}")
    elif completed:
        #playlists can be long, so just point at the folder
        print(f"Saved {len(completed)} files to: {os.path.dirname(completed[0])}")

def download_video(video_url, config, confirm_search=None):
    """Executes the download process. Returns True on success, False on failure.
    A download that fails with a temporary error is tried again, up to
    MAX_ATTEMPTS times in all. Ctrl+C is reported and re-raised so callers can
    decide what it cancels. confirm_search, if given, is called once a search
    has found a video and returns whether to download it."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = _attempt(video_url, config, confirm_search)
        if result is not _RETRY:
            return result
        if attempt == MAX_ATTEMPTS:
            break
        delay = RETRY_DELAY * attempt
        print(f"\nThat looks temporary. Trying again in {delay} seconds (attempt {attempt + 1} of {MAX_ATTEMPTS})...")
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            print("\nDownload cancelled.")
            raise
        #a search result that was confirmed once isn't asked about again
        confirm_search = None
    return False

def _attempt(video_url, config, confirm_search):
    """One try at the download: True, False, or _RETRY if it failed in a way
    that's worth another try."""
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
        return _download(video_url, config, ydl_opts, confirm_search)
    except KeyboardInterrupt:
        cancelled = True
        print("\nDownload cancelled.")
        raise
    finally:
        _remove_temp_dir(temp_dir, report=cancelled)

def _download(video_url, config, ydl_opts, confirm_search=None):
    #the final path of every video that fully finishes
    completed = []
    logger = ydl_opts['logger']
    is_search = not looks_like_url(video_url)
    if not is_search and '://' not in video_url:
        #without a scheme yt-dlp would search for the link's text instead of opening it
        video_url = 'https://' + video_url
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for pp, when in build_extra_postprocessors(config):
                ydl.add_post_processor(pp, when=when)
            #called with the final file once a video is fully processed
            ydl.add_post_hook(lambda path: completed.append(os.path.abspath(path)))
            if is_search:
                print(f"\nSearching YouTube for: {video_url}...")
                #an explicit search, so text like "artist: song" isn't read as a link
                results = _extract_unprocessed(ydl, f'ytsearch1:{video_url}')
                top_result = next(iter(results.get('entries') or []), None)
                if top_result is not None:
                    #shown before downloading, since a typo finds a video too
                    print(f"Found: {_describe(top_result)}")
                    if confirm_search is not None and not confirm_search():
                        print("Skipped.")
                        return False
                    ydl.process_ie_result(top_result, download=True)
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
                #empty if the extraction failed, which the logger has reported
                if info:
                    #carries on from the extraction above instead of repeating it
                    ydl.process_ie_result(info, download=True)

    #most errors reach the logger without being raised, but not all of them
    except yt_dlp.utils.YoutubeDLError as e:
        logger.error(str(e))
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return False

    if not completed:
        #a search with no results or an empty playlist finishes without an error
        if not logger.errors:
            if is_search:
                print(f"\n[Error] No results for: {video_url}")
            else:
                print("\n[Error] Nothing to download from that link.")
        #only when nothing was saved, so finished playlist items aren't downloaded again
        elif _is_transient(logger.errors):
            return _RETRY
        return False
    if logger.errors:
        #e.g. a playlist with a private video in it
        print("\nFinished, but not everything could be downloaded (see the errors above).")
    else:
        print("\nSuccessfully downloaded!")
    _print_saved(completed)
    return not logger.errors
