#!/bin/bash
# Use absolute path for safety if needed, or rely on PATH
set -e

echo "Running migrations..."
alembic upgrade head

echo "Starting application..."
python main.py
