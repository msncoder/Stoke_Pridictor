# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies (Basic tools + Build tools for Python packages)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    ca-certificates \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Copy requirements and install
# We upgrade pip first to handle modern wheels and better error reporting
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set dynamic port for Render
ENV PORT=8000
ENV DISPLAY=:99

# Command to run the app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
