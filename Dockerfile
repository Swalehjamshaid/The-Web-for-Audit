# Use a slim Python image for efficiency
FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies required by libraries like lxml, psycopg2, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libharfbuzz0b libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    libgirepository-1.0-1 libxml2 libxslt1.1 libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Use Gunicorn to serve Flask app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "2"]
