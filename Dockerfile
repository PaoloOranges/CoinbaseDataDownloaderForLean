# Use Python 3.14 Alpine as base image
FROM python:3.14-alpine

# Set working directory
WORKDIR /app

# Copy only necessary files for installation
COPY requirements.txt setup.py .
COPY coinbase_downloader/ ./coinbase_downloader/
COPY tests/ ./tests/
COPY pytest.ini conftest.py ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the package
RUN pip install --no-cache-dir -e .

# Ensure data directory exists for mounting
RUN mkdir -p /app/data

# Set entrypoint to the console script
ENTRYPOINT ["coinbase-downloader", "download"]