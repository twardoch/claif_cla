# this_file: Dockerfile
# Multi-stage Dockerfile for claif_cla package

# Build stage
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies and build
RUN uv venv --python 3.12
RUN . .venv/bin/activate && uv pip install ".[dev,test]"
RUN . .venv/bin/activate && python -m build --outdir dist

# Test stage
FROM builder AS test

# Run tests
RUN . .venv/bin/activate && python -m pytest tests/ -v

# Production stage
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy built package from builder stage
COPY --from=builder /app/dist/*.whl /tmp/

# Install the package
RUN uv pip install --user /tmp/*.whl

# Add user's local bin to PATH
ENV PATH="/home/app/.local/bin:$PATH"

# Set entrypoint
ENTRYPOINT ["python", "-m", "claif_cla.cli"]
CMD ["--help"]

# Development stage
FROM builder AS development

# Install development dependencies
RUN . .venv/bin/activate && uv pip install ".[dev,test]"

# Set up pre-commit hooks
RUN . .venv/bin/activate && pre-commit install

# Set working directory
WORKDIR /app

# Expose port for development server (if needed)
EXPOSE 8000

# Set entrypoint for development
ENTRYPOINT ["/bin/bash"]