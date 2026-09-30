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


def test_missing_default_batch_file_is_created(isolated_config, capsys):
    batch_file = batch.config.get_batch_file()

    assert batch.run_batch(batch_file, {}) is False

    with open(batch_file) as f:
        assert f.read() == batch.BATCH_FILE_HEADER
    assert "Created" in capsys.readouterr().out


def test_created_batch_file_has_no_links_until_edited(isolated_config, monkeypatch, capsys):
    batch_file = batch.config.get_batch_file()
    batch.run_batch(batch_file, {})
    attempted = []
    monkeypatch.setattr(batch.downloader, "download_video", lambda link, config: attempted.append(link))

    assert batch.run_batch(batch_file, {}) is False
    assert attempted == []


def test_missing_custom_batch_file_is_not_created(isolated_config, tmp_path, capsys):
    custom = tmp_path / "typo.txt"

    assert batch.run_batch(str(custom), {}) is False

    assert not custom.exists()
    assert "not found" in capsys.readouterr().out


def test_bom_does_not_end_up_in_the_first_link(tmp_path, monkeypatch):
    batch_file = tmp_path / "batch.txt"
    batch_file.write_bytes("https://example.com/a\n".encode("utf-8-sig"))
    attempted = []
    monkeypatch.setattr(batch.downloader, "download_video", lambda link, config: attempted.append(link) or True)

    batch.run_batch(str(batch_file), {})

    assert attempted == ["https://example.com/a"]


def test_non_utf8_comments_do_not_break_reading(tmp_path, monkeypatch):
    batch_file = tmp_path / "batch.txt"
    batch_file.write_bytes("# Müzik listem\nhttps://example.com/b\n".encode("cp1254"))
    attempted = []
    monkeypatch.setattr(batch.downloader, "download_video", lambda link, config: attempted.append(link) or True)

    batch.run_batch(str(batch_file), {})

    assert attempted == ["https://example.com/b"]
