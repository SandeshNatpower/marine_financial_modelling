# Use a Debian-based image that typically has better support for pre-built wheels
FROM python:3.10-slim

# Install any build dependencies if needed (for example, if you still need to compile something)
RUN apt-get update && apt-get install -y gcc gfortran && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker caching
COPY requirements.txt .

# Upgrade pip, setuptools, and wheel; then install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose Dash's default port
EXPOSE 8050

CMD ["python", "-u", "app.py"]
