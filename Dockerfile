FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    make \
    python3-dev \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and set PATH
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/usr/local/cargo/bin:$PATH"

# Install Playwright and Rust
RUN pip install playwright chromium && playwright install chromium --with-deps && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install only required system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

RUN     curl -LsSf https://astral.sh/uv/install.sh | sh && \
        . $HOME/.local/bin/env && \
        uv venv && \
        uv pip install -r requirements.txt && \
        rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .


# Start the realtime.py script using UV
CMD ["/root/.local/bin/uv", "run", "realtime.py"]
