# Dockerfile for Voice Calendar Telegram Bot
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# No additional system dependencies needed
# Python packages will be installed from wheels

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port for webhook mode (if needed)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the bot
CMD ["python", "-m", "src.main"]
