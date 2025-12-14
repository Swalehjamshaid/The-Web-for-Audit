# 1. CRITICAL FIX: The base image instruction MUST be the first line.
# Use this line to fix the "no build stage" error.
FROM python:3.10-slim-bullseye

# 2. INSTALL SYSTEM DEPENDENCIES
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libgirepository-1.0-1 \
    libxml2 \
    libxslt1.1 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 3. SET UP WORK DIRECTORY
WORKDIR /app

# 4. INSTALL PYTHON DEPENDENCIES
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# 5. COPY APPLICATION CODE
COPY . /app

# 6. APPLICATION ENTRYPOINT - FIXED for cloud platforms
# Uses $PORT if provided by the platform, falls back to 8000 for local development
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT:-8000}", "app:application"]
