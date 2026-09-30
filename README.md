# YT Fetch

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![uv](https://img.shields.io/badge/Build-uv-purple?)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)
![FFmpeg](https://img.shields.io/badge/Powered_by-FFmpeg-414141?logo=ffmpeg)
![Licence](https://img.shields.io/badge/Licence-MIT-blue)
[![Build Wheel](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-wheel.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-wheel.yaml)
[![Build Docker](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-docker.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-docker.yaml)
[![Tests](https://github.com/Furkan5E/YT-Fetch/actions/workflows/test.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/test.yaml)

A modular, interactive command line application for downloading audio and video from YouTube. Powered by `yt-dlp` and `FFmpeg`.

[![Download Latest Release](https://img.shields.io/github/v/release/Furkan5E/YT-Fetch?style=for-the-badge&label=DOWNLOAD%20.WHL&color=success)](https://github.com/Furkan5E/YT-Fetch/releases/latest)

---
## Prerequisites
* **Python 3.10+**
* **uv**: used to install dependencies and run the app.
* **Deno**: installed automatically with the other dependencies. yt-dlp uses it to solve YouTube's JavaScript challenges, without which some formats can be missing.
* **FFmpeg** (optional): used for media processing and metadata embedding. YT Fetch looks for it at `ffmpeg_path` in `config.toml`, then in the yt-fetch config folder (the folder `yt-fetch --config-path` points into), then on your system `PATH`. If it's in none of those, a static build is downloaded automatically on first run.

## Installation
Clone the repository and sync the dependencies.
```bash
git clone https://github.com/Furkan5E/yt-fetch
cd yt-fetch
uv sync
```
Run the main script.
```bash
uv run yt-fetch
```
Settings are saved to `config.toml` in your user config folder (`%APPDATA%\yt-fetch` on Windows, `~/Library/Application Support/yt-fetch` on macOS, `~/.config/yt-fetch` on Linux). Downloads go to `~/Downloads/yt-fetch` by default. You can edit `config.toml` by hand; each setting has a comment listing its options, and your own comments are kept when the app saves changes.
---
## Testing
Run the test suite.
```bash
uv run pytest
```
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
Pre-built container:
```bash
docker run -it --rm -v "${PWD}/downloads:/downloads" -v yt-fetch-config:/config ghcr.io/furkan5e/yt-fetch:latest
```
To use a batch file, put it in `./downloads` and run with `--batch /downloads/batch.txt`.
---
## CLI Flags
Run these directly from your shell for one off, non-interactive downloads. Flags override `config.toml` for that run only, the saved config is never touched.

| Flag | Description |
|---|---|
| `<URL>` | Downloads the given URL once, then exits. Search terms work too: `yt-fetch "daft punk one more time"` downloads the top YouTube result. |
| `--batch [FILE]` | Downloads every link in `FILE` (default: `batch.txt`), then exits. |
| `--type {mp3,m4a,opus,flac,wav,mp4,mkv,webm}` | Overrides the output format. Audio: `mp3`, `m4a`, `opus`, `flac`, `wav`. Video: `mp4`, `mkv`, `webm`. |
| `--quality {128,192,256,320}` | Overrides the audio bitrate (kbps). Not used for `flac` and `wav`, which are lossless. |
| `--resolution {480,720,1080,1440,2160,best}` | Overrides the video resolution. |
| `--metadata {true,false}` | Overrides whether metadata is embedded. |
| `--allow-playlists {true,false}` | Overrides whether playlist URLs are expanded. |
| `--remove-sponsors {true,false}` | Overrides SponsorBlock segment removal. |
| `--embed-lyrics {true,false}` | Overrides whether lyrics are embedded. |
| `--output-dir PATH` | Overrides the download output directory. |
| `--config-path` | Prints the location of `config.toml`, then exits. |
| `--version` | Prints the installed version, then exits. |

## Interactive Commands
Run `yt-fetch` with no arguments to enter the REPL.

| Command | Description |
|---|---|
| `<URL>` | Paste a URL to begin downloading the media based on your current settings. Anything that isn't a link is searched on YouTube and the top result is downloaded. |
| `batch` | Downloads all URLs listed in `batch.txt` (one per line, lines starting with `#` are ignored) using the current settings. |
| `.config` | Displays your current active settings and the location of `config.toml`. |
| `.config [key]` | Displays the value of a specific setting (e.g. `.config quality`). |
| `.config [key] [value]` | Updates and saves a setting (e.g. `.config type mp4` or `.config resolution 720`). |
| `.config reset [key]` | Resets one setting, or all of them, to the default (e.g. `.config reset quality`). |
| `help` | Lists every command and setting (`?` works too). |
| `quit` | Exits the application. |

---

## Disclaimer

This tool is intended for personal, educational, and archival use. Please respect copyright laws and YouTube's Terms of Service. Ensure you have the right to download the media you are fetching.
