# Use a stable Python version
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker caching
COPY requirements.txt .

# Upgrade pip and install dependencies with longer timeout
RUN pip install --upgrade pip && \
    pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose Dash's default port
EXPOSE 8050

# Run the Dash app (make sure your main app file is named app.py)
CMD ["python", "app.py"]
