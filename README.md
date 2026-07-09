# YT Fetch

A modular, interactive command line application for downloading audio and video from YouTube. Powered by `yt-dlp` and `FFmpeg`.

## Dependencies
**yt-dlp**
```bash
pip install yt-dlp
```

**FFmpeg**
You must have FFmpeg for media processing.

FFprobe for metadata embedding.

Download FFmpeg from their [official website](https://ffmpeg.org/download.html)

## Installation 

```bash
git clone https://github.com/Furkan5E/yt-fetch
cd yt-fetch/python
python main.py
```

## Commands

- **Paste a URL:** begins downloading the media based on your current settings.
- **.config:** Displays your current active settings.
- **.config [key]:** Displays the value of a specific setting (e.g., .config quality).
- **.config [key] [value]:** Updates and saves a setting (e.g., .config type mp4 or .config resolution 720).
- **quit:** Exits the application.

## Disclaimer 

This tool is intended for personal, educational, and archival use. Please respect copyright laws and YouTube's Terms of Service. Ensure you have the right to download the media you are fetching.
