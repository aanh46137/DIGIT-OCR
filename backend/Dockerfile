# ─── Stage: Runtime ───────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install OS-level dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Mount point for the local model cache (populated at runtime via volume)
VOLUME ["/models"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
