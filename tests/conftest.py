import pytest

from yt_fetch import config


@pytest.fixture(autouse=True)
def _no_output_dir_env(monkeypatch):
    """Keeps a YT_FETCH_OUTPUT_DIR set on the developer's machine out of the tests."""
    monkeypatch.delenv("YT_FETCH_OUTPUT_DIR", raising=False)


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Points config.py's file resolution at a throwaway directory instead of
    the real project/user config location, so tests never touch the
    developer's actual config.toml/batch.txt."""
    monkeypatch.setattr(config, "get_base_dir", lambda: str(tmp_path))
    return tmp_path
