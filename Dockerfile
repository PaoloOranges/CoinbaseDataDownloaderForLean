# Use Python 3.14 Alpine as base image
FROM python:3.14-alpine

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Ensure data directory exists for mounting
RUN mkdir -p /app/data

# Set entrypoint to run the download command
ENTRYPOINT ["python", "main.py", "download"]