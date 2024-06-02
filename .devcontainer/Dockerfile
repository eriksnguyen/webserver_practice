FROM python:3.12-slim

# Stream stderr and stdout to terminal without buffering
# https://stackoverflow.com/questions/59812009/what-is-the-use-of-pythonunbuffered-in-docker-file
ENV PYTHONUNBUFFERED=true

# Point PYTHONPATH to the development directory
ENV PYTHONPATH=/home/app/connect4

# Expose ports for various web-server types
## GRPC Standard Port
EXPOSE 50051


USER root

# Install necessary packages and remove the apt cache to reduce image size
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    build-essential \
    vim \
    make \
    && rm -rf /var/lib/apt/lists/*

# Switch to the directory we'll mount the repository to. This is specified in
# `docker-compose.dev-backend.yml` at `services.connect4-developer.volumes`
WORKDIR /home/app

# Install the service dependencies
COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip && \
    pip install poetry==1.8.3

RUN poetry config virtualenvs.create false && \
    poetry install \
    --no-root \
    --with dev \
    --sync
