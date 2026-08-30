# YT Fetch

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![uv](https://img.shields.io/badge/Build-uv-purple?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat-square&logo=docker&logoColor=white)
![FFmpeg](https://img.shields.io/badge/Powered_by-FFmpeg-414141?style=flat-square&logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-success?style=flat-square)

A modular, interactive command line application for downloading audio and video from YouTube. Powered by `yt-dlp` and `FFmpeg`.

[![Download Latest Release](https://img.shields.io/github/v/release/Furkan5E/YT-Fetch?style=for-the-badge&label=DOWNLOAD%20.WHL&color=success)](https://github.com/Furkan5E/YT-Fetch/releases/latest)

---
## Prerequisites
* **Python 3.x**
* **[FFmpeg](https://ffmpeg.org/download.html)**: FFmpeg for media processing and FFprobe for metadata embedding

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
## Docker
Build the image.
```bash
docker build -t yt-fetch .
```
Run the container.
```bash
docker run -it -v "${PWD}:/app" yt-fetch
```
---
## Commands

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
