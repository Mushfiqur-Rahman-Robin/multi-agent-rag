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
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create necessary directories
RUN mkdir -p logs uploads && chown -R appuser:appgroup /app

# Copy dependencies first for caching
COPY pyproject.toml requirements.txt ./
RUN uv pip install --no-cache-dir --system -r requirements.txt

# Copy application
COPY . .

# Set permissions for the entire app directory
RUN chown -R appuser:appgroup /app && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
