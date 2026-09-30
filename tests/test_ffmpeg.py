import platform

import pytest

from yt_fetch.downloader import ffmpeg as ffmpeg_module
from yt_fetch.downloader.ffmpeg import FFmpegNotFoundError

FFMPEG_NAME = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"


@pytest.fixture(autouse=True)
def _isolated(isolated_config):
    """The lookup checks the yt-fetch config folder, so keep it in tmp_path."""
    return isolated_config


def _exists_only(*paths):
    allowed = set(paths)
    return lambda path: path in allowed


def test_uses_configured_path_when_it_exists(monkeypatch):
    monkeypatch.setattr(ffmpeg_module.os.path, "exists", _exists_only("/custom/ffmpeg"))

    result = ffmpeg_module._resolve_ffmpeg_path("/custom/ffmpeg")

    assert result == "/custom/ffmpeg"


def test_local_ffmpeg_lives_in_the_config_folder(isolated_config):
    assert ffmpeg_module.get_local_ffmpeg_path() == str(isolated_config / FFMPEG_NAME)


def test_falls_back_past_missing_configured_path_to_config_folder(isolated_config, capsys):
    local = isolated_config / FFMPEG_NAME
    local.write_bytes(b"")

    result = ffmpeg_module._resolve_ffmpeg_path("/does/not/exist")

    assert result == str(local)
    assert "not found" in capsys.readouterr().out.lower()


def test_ffmpeg_in_the_current_folder_is_no_longer_used(isolated_config, tmp_path, monkeypatch):
    elsewhere = tmp_path / "somewhere else"
    elsewhere.mkdir()
    (elsewhere / FFMPEG_NAME).write_bytes(b"")
    monkeypatch.chdir(elsewhere)
    monkeypatch.setattr(ffmpeg_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    assert ffmpeg_module._resolve_ffmpeg_path("auto") == "/usr/bin/ffmpeg"


def test_falls_back_to_system_path_when_nothing_local(monkeypatch):
    monkeypatch.setattr(ffmpeg_module.os.path, "exists", _exists_only())
    monkeypatch.setattr(ffmpeg_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    result = ffmpeg_module._resolve_ffmpeg_path("auto")

    assert result == "/usr/bin/ffmpeg"


def test_falls_back_to_static_ffmpeg_library_as_last_resort(monkeypatch):
    monkeypatch.setattr(ffmpeg_module.os.path, "exists", _exists_only())
    monkeypatch.setattr(ffmpeg_module.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        ffmpeg_module,
        "get_or_fetch_platform_executables_else_raise",
        lambda: ("/cached/ffmpeg.exe", "/cached/ffprobe.exe"),
    )

    result = ffmpeg_module._resolve_ffmpeg_path("auto")

    assert result == "/cached/ffmpeg.exe"


def test_raises_when_static_ffmpeg_fallback_also_fails(monkeypatch):
    monkeypatch.setattr(ffmpeg_module.os.path, "exists", _exists_only())
    monkeypatch.setattr(ffmpeg_module.shutil, "which", lambda name: None)

    def _boom():
        raise OSError("no network")

    monkeypatch.setattr(ffmpeg_module, "get_or_fetch_platform_executables_else_raise", _boom)

    with pytest.raises(FFmpegNotFoundError):
        ffmpeg_module._resolve_ffmpeg_path("auto")


def test_error_says_exactly_where_to_put_ffmpeg(isolated_config, monkeypatch):
    monkeypatch.setattr(ffmpeg_module.os.path, "exists", _exists_only())
    monkeypatch.setattr(ffmpeg_module.shutil, "which", lambda name: None)

    def _offline():
        raise OSError("no network")

    monkeypatch.setattr(ffmpeg_module, "get_or_fetch_platform_executables_else_raise", _offline)

    with pytest.raises(FFmpegNotFoundError) as error:
        ffmpeg_module._resolve_ffmpeg_path("auto")

    assert str(isolated_config / FFMPEG_NAME) in str(error.value)
