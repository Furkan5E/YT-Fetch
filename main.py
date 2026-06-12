import yt_dlp
import sys
import os

def download_youtube_to_mp3(video_url, ffmpeg_path):
    #verify local ffmpeg exists
    if not os.path.exists(ffmpeg_path):
        print(f"Error: Could not find ffmpeg at '{ffmpeg_path}'")
        sys.exit(1)

    #config
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'ffmpeg_location': ffmpeg_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Fetching data for: {video_url}...")
            ydl.download([video_url])
            print("\nSuccessfully downloaded and converted to MP3!")
            
    except yt_dlp.utils.DownloadError as e:
        print(f"\nError downloading the video: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    LOCAL_FFMPEG_PATH = './ffmpeg.exe' 
    
    url = input("Enter the YouTube link: ").strip()
    
    if not url:
        print("Error: No URL provided.")
        sys.exit(1)
        
    download_youtube_to_mp3(url, LOCAL_FFMPEG_PATH)