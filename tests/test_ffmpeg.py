import platform

import pytest

from downloader import ffmpeg as ffmpeg_module
from downloader.ffmpeg import FFmpegNotFoundError

LOCAL_PATH = "./ffmpeg.exe" if platform.system() == "Windows" else "./ffmpeg"


def _exists_only(*paths):
    allowed = set(paths)
    return lambda path: path in allowed


def test_uses_configured_path_when_it_exists(monkeypatch):
    monkeypatch.setattr(ffmpeg_module.os.path, "exists", _exists_only("/custom/ffmpeg"))

    result = ffmpeg_module._resolve_ffmpeg_path("/custom/ffmpeg")

    assert result == "/custom/ffmpeg"


def test_falls_back_past_missing_configured_path_to_local_dir(monkeypatch, capsys):
    monkeypatch.setattr(ffmpeg_module.os.path, "exists", _exists_only(LOCAL_PATH))

    result = ffmpeg_module._resolve_ffmpeg_path("/does/not/exist")

    assert result == LOCAL_PATH
    assert "not found" in capsys.readouterr().out.lower()


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
