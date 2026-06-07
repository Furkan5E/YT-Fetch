import yt_dlp
import sys
import os
import platform
import shutil

CONFIG_FILE = "config.txt"
DEFAULT_CONFIG = {
    "type": "mp3",        #mp3 or mp4
    "quality": "192",     #128, 192, 320
    "resolution": "1080", #1080, 720, 480, best
    "metadata": "true",   #true or false
    "ffmpeg_path": "auto" #auto or file path
}

def load_config():
    """Loads the config.txt file. Creates it with defaults if it doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    config = {}
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                config[key.strip().lower()] = value.strip().lower()
                
    #ensure missing keys are replaced with defaults as fallback
    for k, v in DEFAULT_CONFIG.items():
        if k not in config:
            config[k] = v
    return config

def save_config(config):
    """Saves the dictionary back to config.txt."""
    with open(CONFIG_FILE, 'w') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")


def get_ffmpeg_path(config):
    """Locates ffmpeg via config override, local directory, or system PATH."""
    custom_path = config.get('ffmpeg_path', 'auto')
    
    #1 check if valid path in config
    if custom_path != 'auto':
        if os.path.exists(custom_path):
            return custom_path
        else:
            print(f"\n[Warning] Configured ffmpeg path '{custom_path}' not found.")
            print("          Falling back to auto-detection...")
    
    #2 check local directory
    local_path = './ffmpeg.exe' if platform.system() == 'Windows' else './ffmpeg'
    if os.path.exists(local_path):
        return local_path
    
    #3 check global system PATH
    system_path = shutil.which("ffmpeg")
    if system_path:
        return system_path
    
    #4 not found
    print("\n[Error] ffmpeg not found.")
    print("Please install it, place it in this folder, or set ffmpeg_path in config.txt.")
    sys.exit(1)

def build_ydl_opts(config):
    """Dynamically builds yt-dlp options based on the current config."""
    ffmpeg_path = get_ffmpeg_path(config)
    
    #base options
    opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'ffmpeg_location': ffmpeg_path,
        'quiet': False,
        'postprocessors': []
    }

    #handle type
    if config['type'] == 'mp4':
        res = config.get('resolution', '1080')
        if res == 'best':
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            opts['format'] = f'bestvideo[ext=mp4][height<={res}]+bestaudio[ext=m4a]/best[ext=mp4][height<={res}]/best'
    else:
        #default to mp3
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': config['quality'],
        })

    #handle metadata
    if config['metadata'] == 'true':
        opts['writethumbnail'] = True
        opts['postprocessors'].append({'key': 'FFmpegMetadata'})
        if config['type'] == 'mp3':
            opts['postprocessors'].append({'key': 'EmbedThumbnail'})

    return opts

def download_video(video_url, config):
    """Executes the download process."""
    ydl_opts = build_ydl_opts(config)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nFetching data for: {video_url}...")
            ydl.download([video_url])
            print("\nSuccessfully downloaded!")
            
    except yt_dlp.utils.DownloadError as e:
        print(f"\nError downloading the video: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


def main():
    config = load_config()
    print("YT Fetch")
    
    while True:
        try:
            user_input = input("\nEnter Link: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not user_input:
            continue

        # Command: Quit
        if user_input.lower() == 'quit':
            print("Terminating application.")
            break
            
        # Command: Config
        elif user_input.lower().startswith('.config'):
            parts = user_input.split()
            
            #case 1: ".config" -> print entire config
            if len(parts) == 1:
                print("\nCurrent Configuration:")
                for k, v in config.items():
                    print(f"  {k} = {v}")
                    
            #case 2: ".config key" -> print specific key
            elif len(parts) == 2:
                key = parts[1].lower()
                if key in config:
                    print(f"{config[key]}")
                else:
                    print(f"Unknown config key: '{key}'")
                    
            #case 3: ".config key value" -> update key
            elif len(parts) >= 3:
                key = parts[1].lower()
                value = " ".join(parts[2:]).lower()
                
                if key in config:
                    config[key] = value
                    save_config(config)
                    # Formatting output specifically as you requested
                    if key == "quality":
                        print(f"quality is set to {value}kbs")
                    else:
                        print(f"{key} is set to {value}")
                else:
                    print(f"Unknown config key: '{key}'. Valid keys are: {', '.join(config.keys())}")
                    
        #link entered, download
        else:
            download_video(user_input, config)

if __name__ == "__main__":
    main()