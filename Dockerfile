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
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

# Run the interactive CLI using uv
ENTRYPOINT ["uv", "run", "python", "src/main.py"]