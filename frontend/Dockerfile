FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app
COPY . .

# Expose the Streamlit port
EXPOSE 8501

# Run the Streamlit app with settings optimized for running behind a reverse proxy
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.baseUrlPath=/", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--server.enableWebsocketCompression=false", "--server.headless=true"] 