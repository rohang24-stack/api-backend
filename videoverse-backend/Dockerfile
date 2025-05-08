# Base image for building the application
FROM python:3.12.0-slim-bullseye as base

# Install system dependencies and remove cache to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get install -y iputils-ping && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry && \
    poetry config virtualenvs.create false

# Set the working directory
WORKDIR /app

# Copy only the dependency files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install production dependencies
RUN poetry install --only main

# Remove development tools to reduce image size
RUN apt-get purge -y gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application source code
COPY . .

# Install the project itself
RUN poetry install

# Set the command to run the application
CMD ["/usr/local/bin/python", "-m", "videoverse_backend"]

# Development stage
FROM base as dev

# Expose the application port (if required)
EXPOSE 8000
