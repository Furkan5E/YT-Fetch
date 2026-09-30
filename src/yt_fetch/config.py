import locale
import os
import platform

import tomlkit
from tomlkit.exceptions import TOMLKitError

def _user_config_dir():
    """The OS-standard per-user config location."""
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
    """Where config.toml and batch.txt live."""
    if _base_dir_cache['value'] is None:
        _base_dir_cache['value'] = _user_config_dir()
    return _base_dir_cache['value']

def get_default_output_dir():
    """YT_FETCH_OUTPUT_DIR takes priority, e.g. to point at a mounted Docker volume."""
    return os.environ.get('YT_FETCH_OUTPUT_DIR') or os.path.join(os.path.expanduser('~'), 'Downloads', 'yt-fetch')

def get_config_file():
    return os.path.join(get_base_dir(), "config.toml")

def get_batch_file():
    return os.path.join(get_base_dir(), "batch.txt")

#keys whose values should keep their original casing (they're paths, not enum-like options)
CASE_SENSITIVE_KEYS = ['ffmpeg_path', 'output_dir']

BOOL_KEYS = ['metadata', 'allow_playlists', 'remove_sponsors', 'embed_lyrics']

_STATIC_DEFAULTS = {
    "type": "mp3",
    "quality": 192,
    "resolution": 1080,
    "metadata": True,
    "ffmpeg_path": "auto",
    "allow_playlists": False,
    "remove_sponsors": True,
    "embed_lyrics": False
}

VALID_OPTIONS = {
    "type": ["mp3", "m4a", "opus", "flac", "wav", "mp4", "mkv", "webm"],
    "quality": [128, 192, 256, 320],
    "resolution": [480, 720, 1080, 1440, 2160, "best"],
    "metadata": [True, False],
    "allow_playlists": [True, False],
    "remove_sponsors": [True, False],
    "embed_lyrics": [True, False]
}

#written next to each key when config.toml is first created, and shown by the REPL help command
KEY_DESCRIPTIONS = {
    "type": "audio: mp3, m4a, opus, flac, wav | video: mp4, mkv, webm",
    "quality": "audio bitrate in kbps: 128, 192, 256 or 320 (not used for flac/wav)",
    "resolution": "max video height: 480, 720, 1080, 1440, 2160 or \"best\"",
    "metadata": "embed title, artist and thumbnail",
    "ffmpeg_path": "\"auto\" or a path to an ffmpeg executable",
    "allow_playlists": "download whole playlists from playlist links",
    "remove_sponsors": "cut sponsor segments using SponsorBlock",
    "embed_lyrics": "embed subtitles as lyrics",
    "output_dir": "where downloads are saved"
}

def format_value(value):
    """Renders a config value the way a user would type it."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

def parse_value(key, text):
    """Converts text typed on the CLI or in the REPL into a typed config value."""
    text = text.strip()
    if key in CASE_SENSITIVE_KEYS:
        return text
    text = text.lower()
    if key in BOOL_KEYS and text in ("true", "false"):
        return text == "true"
    if text.isdigit():
        return int(text)
    return text

def is_valid(key, value):
    #compares types too, since True == 1 in Python
    if key not in VALID_OPTIONS:
        return True
    return any(type(value) is type(allowed) and value == allowed for allowed in VALID_OPTIONS[key])

def _default_config():
    """A copy of the default config. output_dir is resolved here."""
    defaults = _STATIC_DEFAULTS.copy()
    defaults["output_dir"] = get_default_output_dir()
    return defaults

def _toml_value(key, value):
    #literal strings for paths, so Windows backslashes don't need escaping when editing by hand
    if key in CASE_SENSITIVE_KEYS and isinstance(value, str) and "'" not in value and "\n" not in value:
        return tomlkit.string(value, literal=True)
    return tomlkit.item(value)

def _new_document(config):
    doc = tomlkit.document()
    doc.add(tomlkit.comment("yt-fetch settings. Edit here or with `.config key value` in the app."))
    doc.add(tomlkit.nl())
    for key, value in config.items():
        item = _toml_value(key, value)
        if key in KEY_DESCRIPTIONS:
            item.comment(KEY_DESCRIPTIONS[key])
        doc.add(key, item)
    return doc

def _read_document(config_file):
    #utf-8-sig drops the BOM some editors add. Older Windows editors save in the
    #system's legacy encoding, which is decoded as that instead; the next save
    #writes the file back as UTF-8
    try:
        with open(config_file, 'r', encoding='utf-8-sig') as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(config_file, 'r', encoding=locale.getpreferredencoding(False)) as f:
            text = f.read()
    return tomlkit.parse(text)

def load_config():
    """Loads config.toml. Creates it with defaults if it doesn't exist."""
    config_file = get_config_file()
    defaults = _default_config()

    if not os.path.exists(config_file):
        save_config(defaults)
        return defaults

    try:
        loaded = _read_document(config_file).unwrap()
    except TOMLKitError as e:
        print(f"\n[Error] {config_file} is not valid TOML: {e}")
        print("        Fix the file, or delete it to restore the defaults.")
        raise SystemExit(1)

    config = {}
    for key, value in loaded.items():
        clean_key = key.strip().lower()
        #accept hand-written strings like "true" or "1080" as well as real TOML types
        config[clean_key] = parse_value(clean_key, value) if isinstance(value, str) else value

    #ensure missing keys are replaced with defaults as fallback
    for k, v in defaults.items():
        if k not in config:
            config[k] = v

    for k in VALID_OPTIONS:
        if not is_valid(k, config[k]):
            print(f"\n[Warning] Invalid value '{format_value(config[k])}' for '{k}' in config.toml. "
                  f"Falling back to default ('{format_value(defaults[k])}').")
            config[k] = defaults[k]

    return config

def save_config(config):
    """Saves the dictionary to config.toml, keeping any comments already in the file."""
    config_file = get_config_file()
    if os.path.exists(config_file):
        doc = _read_document(config_file)
        for key, value in config.items():
            doc[key] = _toml_value(key, value)
    else:
        doc = _new_document(config)

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(doc.as_string())

def reset_config(config, key=None):
    """Resets one key, or every key, to its default and saves. Returns the
    keys that were reset, or None if key isn't a known setting."""
    defaults = _default_config()
    if key is not None and key not in defaults:
        return None
    keys = [key] if key is not None else list(defaults)
    for k in keys:
        config[k] = defaults[k]
    save_config(config)
    return keys

def validate_and_update(config, key, value):
    """Checks if the value is allowed before updating the config."""
    if not is_valid(key, value):
        allowed = ', '.join(format_value(v) for v in VALID_OPTIONS[key])
        print(f"\n[Error] Invalid value for '{key}'. Allowed options are: {allowed}")
        return False

    config[key] = value
    save_config(config)
    return True
