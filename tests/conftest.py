import pytest

import config


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Points config.py's file resolution at a throwaway directory instead of
    the real project/user config location, so tests never touch the
    developer's actual config.txt/batch.txt."""
    monkeypatch.setattr(config, "get_base_dir", lambda: str(tmp_path))
    return tmp_path
