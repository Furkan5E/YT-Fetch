# YT Fetch

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
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
* **Python 3.14+**
* **uv**: used to install dependencies and run the app.
* **FFmpeg** (optional): used for media processing and metadata embedding. If it's not found on your system, in the app folder, or in `config.txt`, YT Fetch automatically downloads a static build for you on first run.

## Installation
Clone the repository and sync the dependencies.
```bash
git clone https://github.com/Furkan5E/yt-fetch
cd yt-fetch
uv sync
```
Run the main script.
```bash
uv run python src/main.py
```
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
Run the container.
```bash
docker run -it -v "${PWD}:/app" yt-fetch
```
Pre-built container:
```bash
docker run -it --rm -v "${PWD}:/app" ghcr.io/furkan5e/yt-fetch:latest
```
---
## CLI Flags
Run these directly from your shell for one off, non-interactive downloads. Flags override `config.txt` for that run only, the saved config is never touched.

| Flag | Description |
|---|---|
| `<URL>` | Downloads the given URL once, then exits. |
| `--batch [FILE]` | Downloads every link in `FILE` (default: `batch.txt`), then exits. |
| `--type {mp3,mp4}` | Overrides the output format. |
| `--quality {128,192,256,320}` | Overrides the audio bitrate (kbps). |
| `--resolution {480,720,1080,1440,2160,best}` | Overrides the video resolution. |
| `--metadata {true,false}` | Overrides whether metadata is embedded. |
| `--allow-playlists {true,false}` | Overrides whether playlist URLs are expanded. |
| `--remove-sponsors {true,false}` | Overrides SponsorBlock segment removal. |
| `--embed-lyrics {true,false}` | Overrides whether lyrics are embedded. |
| `--output-dir PATH` | Overrides the download output directory. |

## Interactive Commands
Run `yt-fetch` with no arguments to enter the REPL.

| Command | Description |
|---|---|
| `<URL>` | Paste a URL to begin downloading the media based on your current settings. |
| `batch` | Downloads all URLs listed in `batch.txt` using the current settings. |
| `.config` | Displays your current active settings. |
| `.config [key]` | Displays the value of a specific setting (e.g. `.config quality`). |
| `.config [key] [value]` | Updates and saves a setting (e.g. `.config type mp4` or `.config resolution 720`). |
| `quit` | Exits the application. |

---

## Disclaimer

This tool is intended for personal, educational, and archival use. Please respect copyright laws and YouTube's Terms of Service. Ensure you have the right to download the media you are fetching.
