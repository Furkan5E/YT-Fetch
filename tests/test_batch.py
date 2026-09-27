from yt_fetch import batch


def _run(tmp_path, monkeypatch, text):
    batch_file = tmp_path / "batch.txt"
    batch_file.write_text(text)
    attempted = []
    monkeypatch.setattr(batch.downloader, "download_video", lambda link, config: attempted.append(link) or True)
    result = batch.run_batch(str(batch_file), {})
    return result, attempted


def test_skips_comment_and_blank_lines(tmp_path, monkeypatch):
    result, attempted = _run(tmp_path, monkeypatch, (
        "# music for the trip\n"
        "https://example.com/a\n"
        "\n"
        "   # indented comment\n"
        "https://example.com/b\n"
    ))

    assert result is True
    assert attempted == ["https://example.com/a", "https://example.com/b"]


def test_keeps_links_containing_a_hash(tmp_path, monkeypatch):
    _, attempted = _run(tmp_path, monkeypatch, "https://example.com/v#t=30\n")

    assert attempted == ["https://example.com/v#t=30"]


def test_file_with_only_comments_has_no_links(tmp_path, monkeypatch, capsys):
    result, attempted = _run(tmp_path, monkeypatch, "# nothing yet\n")

    assert result is False
    assert attempted == []
    assert "has no links" in capsys.readouterr().out
