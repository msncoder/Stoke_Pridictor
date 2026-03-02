# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies for Selenium & Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    default-jdk \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome (Alternative if the above doesn't work on debian-slim)
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable

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
