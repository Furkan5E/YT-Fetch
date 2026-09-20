import os
import platform
import shutil

from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise


class FFmpegNotFoundError(Exception):
    """Raised when ffmpeg cannot be located via config, local dir, PATH, or
    the bundled static-ffmpeg fallback."""
    pass


_ffmpeg_cache = {'source': None, 'resolved': None}

def get_ffmpeg_path(config):
    """Locates ffmpeg via config override, local directory, system PATH, or
    (as a last resort) static-ffmpeg's own downloaded/cached binary.
    Caches the result, keyed on the configured ffmpeg_path, so repeated
    downloads don't repeat the filesystem/PATH/library lookup each time."""
    custom_path = config.get('ffmpeg_path', 'auto')

    if _ffmpeg_cache['source'] == custom_path and _ffmpeg_cache['resolved']:
        return _ffmpeg_cache['resolved']

    resolved = _resolve_ffmpeg_path(custom_path)
    _ffmpeg_cache['source'] = custom_path
    _ffmpeg_cache['resolved'] = resolved
    return resolved

def _resolve_ffmpeg_path(custom_path):
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

    #4 last resort: static-ffmpeg's binary
    try:
        ffmpeg_exe, _ = get_or_fetch_platform_executables_else_raise()
        return ffmpeg_exe
    except Exception as e:
        raise FFmpegNotFoundError(
            f"ffmpeg not found, and the static-ffmpeg fallback failed ({e}). "
            "Please install ffmpeg, place it in this folder, or set "
            "ffmpeg_path in config.txt."
        )
