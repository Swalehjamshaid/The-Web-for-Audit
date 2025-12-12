# 1. FIX 1: Missing 'FROM' instruction (caused "no build stage in current context")
# FIX 2: Switched from retired 'buster' to supported 'bullseye' (fixes apt-get update error)
FROM python:3.10-slim-bullseye

# 2. INSTALL SYSTEM DEPENDENCIES (Needed for WeasyPrint, psycopg2, etc.)
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
# Assumes requirements.txt is in your repository root
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. COPY APPLICATION CODE
COPY . /app

# 6. APPLICATION ENTRYPOINT
# FIX 3: Replaced the placeholder with the correct module path 
# You MUST replace 'your_actual_project_name_here' with the name of your folder that contains wsgi.py
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "your_actual_project_name_here.wsgi"]
