# 1. Base Image
FROM python:3.10-slim-bullseye

# 2. Working Directory
WORKDIR /app

# 3. Install Dependencies for WeasyPrint & psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libharfbuzz0b libpangocairo-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libgirepository-1.0-1 \
    libxml2 libxslt1.1 libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy Requirements & Install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy App
COPY . /app

# 6. Launch Gunicorn with PORT binding
CMD gunicorn app:app --bind 0.0.0.0:$PORT
