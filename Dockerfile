# ... (Part of Dockerfile)
# ---------------------------
# System dependencies
# ---------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango1.0-dev \
    # FIX: Using replacement packages to resolve build failure
    libgdk-pixbuf-xlib-2.0-0 \
    libgdk-pixbuf-xlib-2.0-dev \
    libffi-dev \
    libjpeg-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*
# ... (rest of Dockerfile)
