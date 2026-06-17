import os

CONFIG_FILE = "config.txt"

DEFAULT_CONFIG = {
    "type": "mp3",
    "quality": "192",
    "resolution": "1080",
    "metadata": "true",
    "ffmpeg_path": "auto",
    "allow_playlists": "false"
}

VALID_OPTIONS = {
    "type": ["mp3", "mp4"],
    "quality": ["128", "192", "256", "320"],
    "resolution": ["480", "720", "1080", "1440", "2160", "best"],
    "metadata": ["true", "false"],
    "allow_playlists": ["true", "false"]
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

def validate_and_update(config, key, value):
    """Checks if the value is allowed before updating the config."""
    if key in VALID_OPTIONS and value not in VALID_OPTIONS[key]:
        print(f"\n[Error] Invalid value for '{key}'. Allowed options are: {', '.join(VALID_OPTIONS[key])}")
        return False
    
    config[key] = value
    save_config(config)
    return True