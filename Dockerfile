# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies (Basic tools only first)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Use direct installation from .deb package
# 'apt install' will automatically pull in all required Chrome dependencies
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Set display port to avoid crash
ENV DISPLAY=:99

# Set up work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set dynamic port for Render
ENV PORT=8000

# Command to run the app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
