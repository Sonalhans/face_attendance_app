FROM python:3.10-slim

# Install system dependencies required for OpenCV and dlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libx11-6 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

ENV PORT=8080
EXPOSE $PORT

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"]
