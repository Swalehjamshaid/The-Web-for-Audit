# -----------------------------------------------------
# STEP 1: DEFINE THE BASE IMAGE (THIS WAS MISSING!)
# Choose a stable, small Python image (e.g., Python 3.10)
FROM python:3.10-slim-buster

# -----------------------------------------------------
# STEP 2: INSTALL SYSTEM DEPENDENCIES (Your previous snippet)
# WeasyPrint + PostgreSQL + Gunicorn compilation needs these
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# -----------------------------------------------------
# STEP 3: CONFIGURE APPLICATION ENVIRONMENT
WORKDIR /app
ENV PYTHONUNBUFFERED 1

# -----------------------------------------------------
# STEP 4: INSTALL PYTHON DEPENDENCIES
# Assumes you have a requirements.txt file in your repository root
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# -----------------------------------------------------
# STEP 5: COPY THE REMAINING APPLICATION CODE
COPY . /app

# -----------------------------------------------------
# STEP 6: ENTRYPOINT/COMMAND (How to run the server)
# You will likely replace this with a Gunicorn command for production
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
