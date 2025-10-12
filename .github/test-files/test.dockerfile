# file: .github/test-files/test.dockerfile
# version: 1.0.0
# guid: f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c

# Test Dockerfile
# Purpose: Test hadolint (Docker linter) configuration

# Use specific version tag
FROM ubuntu:22.04

# Add labels for better documentation
LABEL maintainer="test@example.com" \
    version="1.0.0" \
    description="Test Dockerfile for linting"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    APP_HOME=/app \
    USER_NAME=appuser

# Install packages in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    python3 \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ${USER_NAME}

# Create application directory
RUN mkdir -p ${APP_HOME} && \
    chown -R ${USER_NAME}:${USER_NAME} ${APP_HOME}

# Set working directory
WORKDIR ${APP_HOME}

# Copy application files
COPY --chown=${USER_NAME}:${USER_NAME} . ${APP_HOME}/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER ${USER_NAME}

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["--help"]
