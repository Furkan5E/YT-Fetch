import yt_dlp

from .ffmpeg import FFmpegNotFoundError
from .options import build_ydl_opts


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
            print(f"\nFetching data for: {video_url}...")
            ydl.download([video_url])
            print("\nSuccessfully downloaded!")
            return True

    except yt_dlp.utils.DownloadError as e:
        print(f"\nError downloading the video: {e}")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return False
