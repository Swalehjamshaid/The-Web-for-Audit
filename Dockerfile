# Use a lightweight Python 3.10 image
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies for WeasyPrint, PDFs, and Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libharfbuzz0b libpangocairo-1.0-0 libcairo2 \
    libgdk-pixbuf-2.0-0 libgirepository-1.0-1 libxml2 libxslt1.1 \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app source code
COPY . /app

# Expose port
EXPOSE 8080

# Start Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "3"]
