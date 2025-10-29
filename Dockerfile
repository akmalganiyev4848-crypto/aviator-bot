# Base image: Python 3.11
FROM python:3.11-slim

# System dependencies (Tesseract OCR + fonts)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    poppler-utils \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    fonts-liberation \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .
COPY main.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway uses default 5000)
EXPOSE 5000

# Run bot
CMD ["python", "main.py"]
