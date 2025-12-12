
# 1. UPGRADED BASE IMAGE: Switched from 'buster' (Debian 10, retired) 
# to 'bullseye' (Debian 11, supported) to fix the 'apt-get update' error.
FROM python:3.10-slim-bullseye

# 2. INSTALL SYSTEM DEPENDENCIES (Your original list)
# These are necessary for packages like WeasyPrint, psycopg2 (libpq-dev), and compiling Gunicorn.
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
    # Clean up the apt cache to keep the image size small
    && rm -rf /var/lib/apt/lists/*

# 3. SET UP WORK DIRECTORY
WORKDIR /app

# 4. INSTALL PYTHON DEPENDENCIES
# Use a specific, common practice to leverage Docker caching:
# Copy only the requirements file first, run pip install, then copy the rest of the code.
# Ensure you have a 'requirements.txt' file in the root of your repository.
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. COPY APPLICATION CODE
# Copy the rest of your application code into the image
COPY . /app

# 6. APPLICATION ENTRYPOINT (Customize this to your needs)
# This assumes you are running a Gunicorn or similar server.
# If you are using Gunicorn, replace "my_project.wsgi:application" with your project's WSGI path.
# EXPOSE 8000 # Railway automatically handles port exposure, but this is good practice
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "your_project_name.wsgi"]
