FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash agentuser

# Set up workspace
RUN mkdir -p /home/agentuser/workspace && \
    chown -R agentuser:agentuser /home/agentuser

# Copy project files
WORKDIR /home/agentuser
COPY --chown=agentuser:agentuser pyproject.toml poetry.lock* ./
COPY --chown=agentuser:agentuser agentception ./agentception
COPY --chown=agentuser:agentuser src ./src

# Install Python dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi

# Set PATH to include venv binaries
ENV PATH="/home/agentuser/.venv/bin:$PATH"

# Switch to non-root user
USER agentuser

# Set working directory
WORKDIR /home/agentuser/workspace

# Entrypoint: run the agent orchestrator
ENTRYPOINT ["python", "/home/agentuser/agentception/entrypoint.py"]
