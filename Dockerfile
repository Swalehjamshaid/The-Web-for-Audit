FROM python:3.10-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libharfbuzz0b libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    libgirepository-1.0-1 libxml2 libxslt1.1 libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
