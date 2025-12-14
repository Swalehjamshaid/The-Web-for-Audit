# 1. Base Image: Use a slim Python image for efficiency
FROM python:3.10-slim-bullseye

# 2. Set Working Directory
WORKDIR /app

# 3. Install System Dependencies: Required for packages like psycopg2 and weasyprint
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

# 4. Copy and Install Python Dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# 5. Copy Application Code
COPY . /app

# 6. Default Command: Use the correct shell form for robust variable binding.
# This ensures that if railway.toml is missing, the app still attempts to start correctly.
CMD gunicorn app:app --bind 0.0.0.0:$PORT
