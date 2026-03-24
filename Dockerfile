FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Avoid running python buffered to see logs instantly
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
