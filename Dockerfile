FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install wkhtmltopdf for PDF generation
RUN apt-get update && apt-get install -y wkhtmltopdf && apt-get clean

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
