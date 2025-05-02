FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure .streamlit directory exists
RUN mkdir -p /app/.streamlit

# Copy .streamlit configuration (if exists)
COPY .streamlit /app/.streamlit/

# Copy the Streamlit app
COPY . .

# Set environment variables
ENV STREAMLIT_SERVER_ENABLE_CORS=true
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_BASE_URL_PATH=""
ENV STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false
# Note: useSSL is only valid in config.toml, not as an environment variable
# ENV STREAMLIT_SERVER_USE_SSL=false

# Expose the Streamlit port
EXPOSE 8501

# Run the Streamlit app with settings optimized for running behind a reverse proxy
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.enableCORS=true", "--server.enableXsrfProtection=false", "--server.baseUrlPath="] 