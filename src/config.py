import os
import platform

def _is_writable(path):
    """Tests whether path can actually be written to, not just whether it exists."""
    test_file = os.path.join(path, '.yt_fetch_write_test')
    try:
        with open(test_file, 'w') as f:
            f.write('')
        os.remove(test_file)
        return True
    except OSError:
        return False

def _user_config_dir():
    """The OS-standard per-user config location, used as a fallback when the
    source folder isn't writable"""
    system = platform.system()
    if system == 'Windows':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif system == 'Darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    path = os.path.join(base, 'yt-fetch')
    os.makedirs(path, exist_ok=True)
    return path

_base_dir_cache = {'value': None}

def get_base_dir():
    """Where config.txt, batch.txt, and the default downloads folder live."""
    if _base_dir_cache['value'] is None:
        source_dir = os.path.dirname(os.path.abspath(__file__))
        _base_dir_cache['value'] = source_dir if _is_writable(source_dir) else _user_config_dir()
    return _base_dir_cache['value']

def get_config_file():
    return os.path.join(get_base_dir(), "config.txt")

def get_batch_file():
    return os.path.join(get_base_dir(), "batch.txt")

#keys whose values should keep their original casing (they're paths, not enum-like options)
CASE_SENSITIVE_KEYS = ['ffmpeg_path', 'output_dir']

_STATIC_DEFAULTS = {
    "type": "mp3",
    "quality": "192",
    "resolution": "1080",
    "metadata": "true",
    "ffmpeg_path": "auto",
    "allow_playlists": "false",
    "remove_sponsors": "true",
    "embed_lyrics": "false"
}

VALID_OPTIONS = {
    "type": ["mp3", "mp4"],
    "quality": ["128", "192", "256", "320"],
    "resolution": ["480", "720", "1080", "1440", "2160", "best"],
    "metadata": ["true", "false"],
    "allow_playlists": ["true", "false"],
    "remove_sponsors": ["true", "false"],
    "embed_lyrics": ["true", "false"]
}

def _default_config():
    """A copy of the default config. output_dir is resolved here."""
    defaults = _STATIC_DEFAULTS.copy()
    defaults["output_dir"] = os.path.join(get_base_dir(), "downloads")
    return defaults

def load_config():
    """Loads the config.txt file. Creates it with defaults if it doesn't exist."""
    config_file = get_config_file()
    defaults = _default_config()

    if not os.path.exists(config_file):
        save_config(defaults)
        return defaults

    config = {}
    with open(config_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                clean_key = key.strip().lower()
                clean_val = value.strip()

                if clean_key not in CASE_SENSITIVE_KEYS:
                    clean_val = clean_val.lower()

                config[clean_key] = clean_val

    #ensure missing keys are replaced with defaults as fallback
    for k, v in defaults.items():
        if k not in config:
            config[k] = v

    for k, allowed in VALID_OPTIONS.items():
        if config.get(k) not in allowed:
            print(f"\n[Warning] Invalid value '{config.get(k)}' for '{k}' in config.txt. "
                  f"Falling back to default ('{defaults[k]}').")
            config[k] = defaults[k]

    return config

def save_config(config):
    """Saves the dictionary back to config.txt."""
    with open(get_config_file(), 'w') as f:
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