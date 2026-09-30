# YT Fetch

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![uv](https://img.shields.io/badge/Build-uv-purple?)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)
![FFmpeg](https://img.shields.io/badge/Powered_by-FFmpeg-414141?logo=ffmpeg)
![Licence](https://img.shields.io/badge/Licence-MIT-blue)
[![Build Wheel](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-wheel.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-wheel.yaml)
[![Build Docker](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-docker.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-docker.yaml)
[![Tests](https://github.com/Furkan5E/YT-Fetch/actions/workflows/test.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/test.yaml)

A modular, interactive command line application for downloading audio and video from YouTube. Powered by `yt-dlp` and `FFmpeg`.

Download as mp3, m4a, opus, flac or wav audio, or mp4, mkv or webm video up to 4K. Paste a link or just type what you're looking for, embed lyrics and cover art, cut out sponsor segments with SponsorBlock, and download whole lists of links in one go.

[![Download Latest Release](https://img.shields.io/github/v/release/Furkan5E/YT-Fetch?style=for-the-badge&label=DOWNLOAD%20.WHL&color=success)](https://github.com/Furkan5E/YT-Fetch/releases/latest)

---

## Prerequisites
* **Python 3.11+**
* **uv**: used to install and run the app.
* **Deno**: installed automatically with the other dependencies. yt-dlp uses it to solve YouTube's JavaScript challenges, without which some formats can be missing.
* **FFmpeg** (optional): used for media processing and metadata embedding. YT Fetch looks for it at `ffmpeg_path` in `config.toml`, then in the yt-fetch config folder (run `yt-fetch --config-path` to see where that is), then on your system `PATH`. If it's in none of those, a static build is downloaded automatically on first run.

## Installation
Install the `.whl` from the [latest release](https://github.com/Furkan5E/YT-Fetch/releases/latest) as a command you can run from anywhere:
```bash
uv tool install yt_fetch-2.0.0-py3-none-any.whl
yt-fetch
```
Or install it straight from GitHub:
```bash
uv tool install git+https://github.com/Furkan5E/YT-Fetch
```
To run it from a clone of the repository instead:
```bash
git clone https://github.com/Furkan5E/yt-fetch
cd yt-fetch
uv sync
uv run yt-fetch
```

Settings are saved to `config.toml` in your user config folder (`%APPDATA%\yt-fetch` on Windows, `~/Library/Application Support/yt-fetch` on macOS, `~/.config/yt-fetch` on Linux). `batch.txt` lives in the same folder. Downloads go to `~/Downloads/yt-fetch` by default.

### Upgrading from 1.x
Version 2.0 stores settings in `config.toml` in the folder above, instead of `config.txt` next to the app. Settings from 1.x aren't carried over, so set them again with `.config` or by editing `config.toml`.

---

## Interactive Mode
Run `yt-fetch` with no arguments to start interactive mode.

| Command | Description |
|---|---|
| `<URL>` | Paste a URL to begin downloading the media based on your current settings. Anything that isn't a link is searched on YouTube and the top result is downloaded. |
| `batch` | Downloads every link in `batch.txt` in the config folder (one per line, lines starting with `#` are ignored). If the file doesn't exist yet, it's created for you. |
| `.config` | Displays your current settings and the location of `config.toml`. |
| `.config [key]` | Displays the value of a specific setting (e.g. `.config quality`). |
| `.config [key] [value]` | Updates and saves a setting (e.g. `.config type mp4` or `.config resolution 720`). |
| `.config reset [key]` | Resets one setting, or all of them, to the default (e.g. `.config reset quality`). |
| `help` | Lists every command and setting (`?` works too). |
| `quit` | Exits the application. |

Pressing Ctrl+C during a download cancels it and removes its partial files, then returns you to the prompt. Pressing Ctrl+C at the prompt exits.

## CLI Flags
Run these directly from your shell for one-off, non-interactive downloads. Flags override `config.toml` for that run only; the saved config is never touched.

| Flag | Description |
|---|---|
| `<URL>` | Downloads the given URL once, then exits. Search terms work too: `yt-fetch "daft punk one more time"` downloads the top YouTube result. |
| `--batch [FILE]` | Downloads every link in `FILE` (default: `batch.txt` in the config folder), then exits. |
| `--type {mp3,m4a,opus,flac,wav,mp4,mkv,webm}` | Overrides the output format. Audio: `mp3`, `m4a`, `opus`, `flac`, `wav`. Video: `mp4`, `mkv`, `webm`. |
| `--quality {128,192,256,320}` | Overrides the audio bitrate (kbps). Not used for `flac` and `wav`, which are lossless. |
| `--resolution {480,720,1080,1440,2160,best}` | Overrides the maximum video height. |
| `--metadata {true,false}` | Overrides whether metadata is embedded. |
| `--allow-playlists {true,false}` | Overrides whether playlist URLs are expanded. |
| `--remove-sponsors {true,false}` | Overrides SponsorBlock segment removal. |
| `--embed-lyrics {true,false}` | Overrides whether lyrics are embedded. |
| `--output-dir PATH` | Overrides the download output directory. |
| `--config-path` | Prints the location of `config.toml`, then exits. |
| `--version` | Prints the installed version, then exits. |

## Settings
Change these with `.config [key] [value]` in interactive mode, or edit `config.toml` by hand. Each setting in the file has a comment listing its options, and your own comments are kept when the app saves changes.

| Key | Options | Default | Description |
|---|---|---|---|
| `type` | `mp3`, `m4a`, `opus`, `flac`, `wav`, `mp4`, `mkv`, `webm` | `mp3` | Output format. `mp4` prefers H.264 for compatibility, `mkv` takes the best quality in any codec, `webm` uses VP9 and Opus. |
| `quality` | `128`, `192`, `256`, `320` | `192` | Audio bitrate in kbps. Not used for `flac` and `wav`. |
| `resolution` | `480`, `720`, `1080`, `1440`, `2160`, `best` | `1080` | Maximum video height. |
| `metadata` | `true`, `false` | `true` | Embeds the title, artist and cover art. Cover art isn't supported in `wav` and `webm`. |
| `allow_playlists` | `true`, `false` | `false` | Downloads the whole playlist when a link points to one. |
| `remove_sponsors` | `true`, `false` | `true` | Cuts sponsor, interaction reminder, intro and outro segments using SponsorBlock. |
| `embed_lyrics` | `true`, `false` | `false` | Embeds the video's hand-written captions: as lyrics in audio files, or as subtitle tracks in video files. Only works when the video has captions. |
| `ffmpeg_path` | `auto` or a path | `auto` | Where to find FFmpeg. `auto` searches as described in [Prerequisites](#prerequisites). |
| `output_dir` | a folder | `~/Downloads/yt-fetch` | Where downloads are saved. `~` and environment variables like `%USERPROFILE%` are expanded, and relative paths are resolved from the current folder. The `YT_FETCH_OUTPUT_DIR` environment variable changes the default. |

---

## Docker
Build the image.
```bash
docker build -t yt-fetch .
```
Run the container. Downloads are saved to `./downloads` on your machine, and settings are kept in the `yt-fetch-config` volume between runs.
```bash
docker run -it --rm -v "${PWD}/downloads:/downloads" -v yt-fetch-config:/config yt-fetch
```
Pre-built container (use a version tag such as `:2.0.0` instead of `:latest` to stay on one release):
```bash
docker run -it --rm -v "${PWD}/downloads:/downloads" -v yt-fetch-config:/config ghcr.io/furkan5e/yt-fetch:latest
```
To download a batch file, put it in `./downloads` and pass it with `--batch`:
```bash
docker run -it --rm -v "${PWD}/downloads:/downloads" -v yt-fetch-config:/config ghcr.io/furkan5e/yt-fetch:latest --batch /downloads/batch.txt
```
Don't change `output_dir` inside the container: downloads are only saved to your machine while they go to `/downloads`.

---

## Development
Run the test suite.
```bash
uv run pytest
```

---

## Disclaimer

This tool is intended for personal, educational, and archival use. Please respect copyright laws and YouTube's Terms of Service. Ensure you have the right to download the media you are fetching.
