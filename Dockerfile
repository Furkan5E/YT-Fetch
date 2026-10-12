# Build stage: installs the app and its dependencies into /app/.venv
FROM python:3.14-slim AS build

# Pinned so a rebuild of the same commit uses the same uv
RUN pip install --no-cache-dir uv==0.12.17

WORKDIR /app

# Dependencies first, so they're only reinstalled when the lock file changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then the app itself, as a normal (non-editable) install so the final image
# doesn't need the source tree or uv
COPY . .
RUN uv sync --frozen --no-dev --no-editable


# Final image: Python, FFmpeg and the installed app
FROM python:3.14-slim

# FFmpeg (required for yt-dlp media merging and metadata). Not pinned: the
# version available changes with the Debian release the base image is on
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /app/.venv /app/.venv

# Config and downloads live outside /app so they can be mounted as volumes.
# HOME and the cache point at folders anyone can write to, so the image also
# works when started with --user
ENV PATH="/app/.venv/bin:$PATH" \
    XDG_CONFIG_HOME=/config \
    XDG_CACHE_HOME=/tmp/cache \
    HOME=/tmp \
    YT_FETCH_OUTPUT_DIR=/downloads
RUN mkdir -p /config /downloads && chmod 777 /config /downloads

# Run the app directly, rather than through uv, which rebuilt it on every start
ENTRYPOINT ["yt-fetch"]
