FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY backend /app/backend
COPY data /app/data
COPY configs /app/configs

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Create necessary directories
RUN mkdir -p data/uploads data/output data/generated data/cleaned data/final data/pdf data/docx data/html data/txt data/youtube

# Run the application
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
