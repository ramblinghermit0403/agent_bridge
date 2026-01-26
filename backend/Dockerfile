# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Copy the dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
# Install Python dependencies using uv
# Syncing ensures we use exactly what's in python_modules if lockfile exists, or resolves deps
RUN uv pip install -r requirements.txt --system

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
