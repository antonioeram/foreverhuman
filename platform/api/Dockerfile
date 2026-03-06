FROM python:3.12-slim

# BUILD_ENV=dev → requirements.min.txt (rapid, fără ML deps)
# BUILD_ENV=prod → requirements.txt (complet)
ARG BUILD_ENV=dev

WORKDIR /app

# Dependențe sistem
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt requirements.min.txt ./
RUN if [ "$BUILD_ENV" = "prod" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir -r requirements.min.txt; \
    fi

# Cod aplicație
COPY . .

# User non-root
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
