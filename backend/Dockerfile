# Multi-stage build for smaller final image
# Stage 1: Dependencies
FROM python:3.11-slim as deps
WORKDIR /app
# Install only dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim
WORKDIR /app
# Copy only installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
# Copy application code
COPY . .
# Create non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

