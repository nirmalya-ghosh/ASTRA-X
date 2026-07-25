FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for OpenCV, astropy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install engine package
COPY engine/ /app/engine/
RUN pip install --no-cache-dir -e /app/engine/

# Copy backend code
COPY backend/ /app/

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/cache /app/data/exports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
