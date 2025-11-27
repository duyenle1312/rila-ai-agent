# Builder stage
FROM python:3.11.5 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Create virtual environment
RUN python -m venv .venv

# Copy requirements and install
COPY requirements.txt ./
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

# Final image
FROM python:3.11.5-slim
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv .venv/
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
