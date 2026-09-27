import yt_dlp
from yt_dlp.utils import remove_terminal_sequences

from .ffmpeg import FFmpegNotFoundError
from .options import build_ydl_opts, build_extra_postprocessors


def _clean_error(error):
    """Strips yt-dlp's colour codes and 'ERROR:' prefix from its messages."""
    return remove_terminal_sequences(str(error)).removeprefix('ERROR:').strip()

def download_video(video_url, config):
    """Executes the download process. Returns True on success, False on failure."""
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
            print(f"\nFetching data for: {video_url}...")
            ydl.download([video_url])
            print("\nSuccessfully downloaded!")
            return True

    except yt_dlp.utils.DownloadError as e:
        print(f"\n[Error] {_clean_error(e)}")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return False
