FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    git gcc && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app
ENV UVICORN_LOG_LEVEL=debug
ENV PYTHONUNBUFFERED=1
ENV FASTAPI_ENV=development

# Install Python dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .

# Start the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--log-level", "debug"]