FROM mcr.microsoft.com/devcontainers/python:3.11

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    ffmpeg \
    xvfb \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libegl1-mesa \
    libglu1-mesa \
    libglfw3 \
    libglew-dev \
    mesa-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*ee