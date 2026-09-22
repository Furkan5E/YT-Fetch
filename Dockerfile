# Use a lightweight Python base image
FROM python:3.14-slim

# Install FFmpeg (Required for yt-dlp media merging and metadata)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Set the working directory
WORKDIR /app

# Copy dependency files and install them
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy the rest of the application code
COPY . .
RUN uv sync --frozen

# Keep config and downloads outside /app so they can be mounted as volumes
ENV XDG_CONFIG_HOME=/config \
    YT_FETCH_OUTPUT_DIR=/downloads
RUN mkdir -p /config /downloads

# Run the interactive CLI using uv
ENTRYPOINT ["uv", "run", "yt-fetch"]