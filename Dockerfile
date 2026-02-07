FROM python:3.12-slim

# Use build-time arguments for UID/GID to match host user if needed,
# defaulting to 1000 which is standard for the first user on Linux.
ARG USER_ID=1000
ARG GROUP_ID=1000

# Create a non-root user with specific UID/GID
RUN groupadd -g ${GROUP_ID} appgroup && \
    useradd -u ${USER_ID} -g appgroup -m appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create necessary directories
RUN mkdir -p logs uploads && chown -R appuser:appgroup /app

# Copy dependencies first for caching
COPY --chown=appuser:appgroup pyproject.toml requirements.txt ./
ENV UV_HTTP_TIMEOUT=300
RUN uv pip install --no-cache-dir --system -r requirements.txt

# Copy application
COPY --chown=appuser:appgroup . .

# Set permissions for entrypoint
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8777

ENTRYPOINT ["./entrypoint.sh"]
