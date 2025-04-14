# Use a stable Python version with minimal vulnerabilities
FROM python:3.10-alpinene

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose Dash's default port
EXPOSE 8050

CMD ["python", "-u", "app.py"]
