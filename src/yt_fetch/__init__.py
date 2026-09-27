from importlib.metadata import PackageNotFoundError, version


def get_version():
    """The installed version, read from pyproject.toml's metadata."""
    try:
        return version("yt-fetch")
    except PackageNotFoundError:
        return "unknown"
