# YT Fetch

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![uv](https://img.shields.io/badge/Build-uv-purple?)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)
![FFmpeg](https://img.shields.io/badge/Powered_by-FFmpeg-414141?logo=ffmpeg)
![Licence](https://img.shields.io/badge/Licence-MIT-blue)
[![Build Wheel](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-wheel.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-wheel.yaml)
[![Build Docker](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-docker.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/build-docker.yaml)
[![Tests](https://github.com/Furkan5E/YT-Fetch/actions/workflows/test.yaml/badge.svg)](https://github.com/Furkan5E/YT-Fetch/actions/workflows/test.yaml)

An interactive command line application for downloading audio and video from YouTube. Powered by `yt-dlp` and `FFmpeg`.

Download as mp3, m4a, opus, flac or wav audio, or mp4, mkv or webm video up to 4K. Paste a link or just type what you're looking for, embed lyrics and cover art, cut out sponsor segments with SponsorBlock, and download whole lists of links in one go.

[![Download Latest Release](https://img.shields.io/github/v/release/Furkan5E/YT-Fetch?style=for-the-badge&label=DOWNLOAD%20.WHL&color=success&logo=github)](https://github.com/Furkan5E/YT-Fetch/releases/latest)

```bash
yt-fetch                                        # interactive mode
yt-fetch "https://youtu.be/..." --type mp4      # download one link, then exit
yt-fetch "daft punk one more time"              # search and download the top result
```

---

## Prerequisites
* **Python 3.11+**
* **uv**: used to install and run the app.
* **Deno**: installed automatically with the other dependencies. yt-dlp uses it to solve YouTube's JavaScript challenges, without which some formats can be missing.
* **FFmpeg** (optional): used for media processing and metadata embedding. YT Fetch looks for it in this order:
  1. `ffmpeg_path` in `config.toml`
  2. the yt-fetch config folder (run `yt-fetch --config-path` to see where that is)
  3. your system `PATH`
  4. if it's in none of those, a static build is downloaded automatically on first run

## Installation
Download the `.whl` from the [latest release](https://github.com/Furkan5E/YT-Fetch/releases/latest) and install it as a command you can run from anywhere, using the name of the file you downloaded:
```bash
uv tool install yt_fetch-X.Y.Z-py3-none-any.whl
yt-fetch
```
Or install it straight from GitHub:
```bash
uv tool install git+https://github.com/Furkan5E/YT-Fetch
```
To run it from a clone of the repository instead:
```bash
git clone https://github.com/Furkan5E/YT-Fetch
cd YT-Fetch
uv sync
uv run yt-fetch
```

Settings are saved to `config.toml` in your user config folder (`%APPDATA%\yt-fetch` on Windows, `~/Library/Application Support/yt-fetch` on macOS, `~/.config/yt-fetch` on Linux). `batch.txt` lives in the same folder. Downloads go to `~/Downloads/yt-fetch` by default.

---

## Interactive Mode
Run `yt-fetch` with no arguments to start interactive mode.

| Command | Description |
|---|---|
| `<URL>` | Paste a URL to begin downloading the media based on your current settings. Anything that isn't a link is searched on YouTube: the top result is shown and downloaded once you confirm with Enter. |
| `batch` | Downloads every link in `batch.txt` in the config folder (one per line, lines starting with `#` are ignored). If the file doesn't exist yet, it's created for you. |
| `.config` | Displays your current settings and the location of `config.toml`. |
| `.config [key]` | Displays the value of a specific setting (e.g. `.config quality`). |
| `.config [key] [value]` | Updates and saves a setting (e.g. `.config type mp4` or `.config resolution 720`). |
| `.config reset [key]` | Resets one setting, or all of them, to the default (e.g. `.config reset quality`). |
| `help` | Lists every command and setting (`?` works too). |
| `quit` | Exits the application (`exit` and `q` work too). |

Pressing Ctrl+C during a download cancels it and removes its partial files, then returns you to the prompt. Pressing Ctrl+C at the prompt exits.

A download that fails with a temporary error, such as a dropped connection or YouTube refusing the request, is tried again automatically, up to three attempts in all.

## CLI Flags
Pass a link (or `--batch`) to download without the prompt and exit. The other flags override `config.toml` for that run only, and the saved config is never touched. They work in interactive mode too: `yt-fetch --type mp4` opens the prompt with `type` set to `mp4` for that session.

| Flag | Description |
|---|---|
| `<URL>` | Downloads the given URL once, then exits. Search terms work too: `yt-fetch "daft punk one more time"` downloads the top YouTube result. |
| `--batch [FILE]` | Downloads every link in `FILE` (default: `batch.txt` in the config folder), then exits. |
| `--type {mp3,m4a,opus,flac,wav,mp4,mkv,webm}` | Overrides the output format. Audio: `mp3`, `m4a`, `opus`, `flac`, `wav`. Video: `mp4`, `mkv`, `webm`. |
| `--quality {128,192,256,320}` | Overrides the audio bitrate (kbps). Only used for `mp3` and `m4a`. |
| `--resolution {480,720,1080,1440,2160,best}` | Overrides the maximum video height. |
| `--metadata {true,false}` | Overrides whether metadata is embedded. |
| `--allow-playlists {true,false}` | Overrides whether playlist URLs are expanded. |
| `--remove-sponsors {true,false}` | Overrides SponsorBlock segment removal. |
| `--embed-lyrics {true,false}` | Overrides whether lyrics are embedded. |
| `--output-dir PATH` | Overrides the download output directory. |
| `--config-path` | Prints the location of `config.toml`, then exits. |
| `--version` | Prints the installed version, then exits. |

For scripts, the exit code says how a non-interactive run ended:

| Exit code | Meaning |
|---|---|
| `0` | Everything was downloaded. |
| `1` | Something failed, or nothing was found. |
| `2` | The arguments weren't valid. |
| `130` | Cancelled with Ctrl+C. |

## Settings
Change these with `.config [key] [value]` in interactive mode, or edit `config.toml` by hand. Each setting in the file has a comment listing its options, and your own comments are kept when the app saves changes.

| Key | Options | Default | Description |
|---|---|---|---|
| `type` | `mp3`, `m4a`, `opus`, `flac`, `wav`, `mp4`, `mkv`, `webm` | `mp3` | Output format. |
| `quality` | `128`, `192`, `256`, `320` | `192` | Audio bitrate in kbps, for `mp3` and `m4a`. |
| `resolution` | `480`, `720`, `1080`, `1440`, `2160`, `best` | `1080` | Maximum video height. |
| `metadata` | `true`, `false` | `true` | Embeds the title, artist and cover art. |
| `allow_playlists` | `true`, `false` | `false` | Downloads the whole playlist when a link points to one. |
| `remove_sponsors` | `true`, `false` | `true` | Cuts sponsor, interaction reminder, intro and outro segments using SponsorBlock. |
| `embed_lyrics` | `true`, `false` | `false` | Embeds the video's captions as lyrics. |
| `ffmpeg_path` | `auto` or a path | `auto` | Where to find FFmpeg. |
| `output_dir` | a folder | `~/Downloads/yt-fetch` | Where downloads are saved. |

More on each setting:

* **`type`**: `mp4` prefers H.264 for compatibility, and `mkv` takes the best quality in any codec. `webm` uses VP9 and Opus, and re-encodes (slowly) the rare video that doesn't come in those.
* **`quality`**: not used for `opus`, which is saved exactly as YouTube provides it, or for `flac` and `wav`. YouTube's own audio is around 130 kbps, so higher values and the lossless types give bigger files, not better sound.
* **`metadata`**: cover art isn't supported in `wav` and `webm`.
* **`allow_playlists`**: when off, a video link that also names a playlist downloads just the video, and links to a playlist or channel itself are refused.
* **`remove_sponsors`**: if SponsorBlock can't be reached, the download goes ahead with a warning and nothing is cut.
* **`embed_lyrics`**: these are the captions someone wrote for the video, not lyrics from a lyrics service, so it only works when the video has them. Audio files get them as a lyrics tag, video files as subtitle tracks.
* **`ffmpeg_path`**: `auto` searches as described in [Prerequisites](#prerequisites).
* **`output_dir`**: `~` and environment variables like `%USERPROFILE%` are expanded, and relative paths are resolved from the current folder. The `YT_FETCH_OUTPUT_DIR` environment variable, when set, is used instead of this setting.

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
Pre-built container (use a version tag such as `:2.1.0` instead of `:latest` to stay on one release):
```bash
docker run -it --rm -v "${PWD}/downloads:/downloads" -v yt-fetch-config:/config ghcr.io/furkan5e/yt-fetch:latest
```
To download a batch file, put it in `./downloads` and pass it with `--batch`:
```bash
docker run -it --rm -v "${PWD}/downloads:/downloads" -v yt-fetch-config:/config ghcr.io/furkan5e/yt-fetch:latest --batch /downloads/batch.txt
```
The image sets `YT_FETCH_OUTPUT_DIR` to `/downloads`, so downloads land in the mounted folder whatever `output_dir` says.

On Linux, downloads are owned by root unless you start the container as yourself by adding `--user "$(id -u):$(id -g)"` after `--rm`.

These commands work as written in PowerShell and bash. In `cmd`, write `%cd%` instead of `${PWD}`.

---

## Development
Run the test suite.
```bash
uv run pytest
```
Found a bug or have an idea? Open an [issue](https://github.com/Furkan5E/YT-Fetch/issues).

---

## Disclaimer

This tool is intended for personal, educational, and archival use. Please respect copyright laws and YouTube's Terms of Service. Ensure you have the right to download the media you are fetching.
