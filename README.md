# 📰 SQR AI News

Hello! This is a **cool news app** that uses computers to find news for you!

## 🌟 Project Overview

SQR AI News is a smart news aggregator that:

- **Collects** fresh news stories from many different websites
- **Analyzes** the content using artificial intelligence
- **Organizes** stories by topics that interest you
- **Presents** everything in a clean, easy-to-read format

Our goal is to help you stay informed without being overwhelmed by too much information!

## 🤔 What Does It Do?

This app:

- Collects news stories from all over the internet
- Uses AI (smart computer brain) to sort the news
- Shows you news you might like to read
- Remembers what you read so it can suggest similar stories
- Updates automatically with fresh news
- Works on your computer, phone, or tablet

## 🚀 How To Use It

### Step 1: Get Ready

Make sure you have these things installed on your computer:
- **Python** version 3.11
- **Poetry** for installing packages
- **Git** for downloading the code (optional)
- **Docker & Docker Compose** (optional, for containerized setup)

### Step 2: Download the App

```sh
# Get the code
git clone https://github.com/SergePolin/sqr-ai-news
cd sqr-ai-news
```

### Step 3: Get The App Running

Use these simple commands:

#### On MacOS/Linux

```sh
# Install everything the app needs
make install

# Activate the virtual environment (or run with 'poetry run')
poetry shell

# Start the app
python run.py

# OR use the make command
make run
```

#### On Windows

```bash
# Install everything the app needs
poetry install

# Activate the virtual environment (or run with 'poetry run')
poetry shell

# Start the app
python run.py

# OR use poetry run directly
poetry run python run.py
```

### Step 4: Have Fun

- Visit the website at: <http://localhost:8000>
- API documentation at: <http://localhost:8000/docs>
- See all the pretty news stories!
- Click on categories to filter news
- Search for topics you're interested in
- Save your favorite stories

## 🐳 Running with Docker

You can also run the application using Docker, which makes setup much easier:

### Using Docker Compose (Recommended)

```sh
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Using Docker Directly

```sh
# Build the Docker image
docker build -t sqr-ai-news .

# Run the container
docker run -p 8000:8000 sqr-ai-news
```

## ✅ Check If Everything Works

Run these tests to make sure everything is working correctly:

#### On MacOS/Linux

```sh
# Run all tests
make test

# Run tests with coverage report
poetry run pytest --cov=app tests/
```

#### On Windows

```bash
# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=app tests/
```

## 🧹 Keep Things Tidy

Clean up temporary files:

#### On MacOS/Linux

```sh
# General cleanup
make clean

# Also remove virtual environment
rm -rf .venv
```

#### On Windows

```bash
# Remove cache files
del /s /q __pycache__
del /s /q *.pyc

# Also remove virtual environment (if needed)
rmdir /s /q .venv
```

## 📚 Project Structure

Here's how our project is organized:

```
sqr-ai-news/
├── app/                 # Main application code
│   ├── api/             # API endpoints
│   ├── db/              # Database models and operations
│   ├── services/        # Business logic
│   └── main.py          # Application entry point
├── tests/               # Test files
├── Makefile             # Helpful commands
├── pyproject.toml       # Project dependencies
└── README.md            # This file!
```

## 🛠️ Made With

This app uses these cool technologies:

- **FastAPI** (to make websites) - Super fast web framework
- **Streamlit** (to make pretty buttons and pages) - Easy-to-use dashboard
- **SQLAlchemy** (to remember news stories) - Talks to the database
- **Pydantic** (to check information) - Makes sure data is correct
- **Pytest** (to check if everything works) - Runs tests automatically
- **Python 3.11** (the main language) - Powers everything

Made with ❤️ by Bantiki 🎀 team


# AI-Powered News Aggregator

This project is a news aggregator service with AI-powered features. It fetches news from multiple sources and provides user authentication, news categorization, and AI-enhanced summarization.

## Features

- **User Authentication**: Register and login to access personalized news feeds
- **Feed Subscription**: Subscribe to Telegram channels for news
- **AI Summarization**: Generate concise summaries of articles using Azure OpenAI
- **Search Functionality**: Find articles using keywords
- **Category Filtering**: Filter articles by categories

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- Azure OpenAI API access (for AI summarization)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-news-aggregator.git
   cd ai-news-aggregator
   ```

2. Install dependencies using Poetry:
   ```
   poetry install
   ```

3. Set up environment variables for Azure OpenAI (required for AI summarization):
   Create a `.env` file in the root directory with:
   ```
   AZURE_OPENAI_KEY=your-azure-openai-key
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2023-12-01-preview
   AZURE_OPENAI_DEPLOYMENT=gpt-4
   ```

### Running the Application

1. Run the backend server:
   ```
   poetry run python run.py
   ```

2. Run the frontend:
   ```
   cd frontend
   poetry run streamlit run streamlit_app.py
   ```

## API Documentation

The API documentation is available at `http://localhost:8000/docs` when the server is running.

## AI Features

### Article Summarization

The application uses Azure OpenAI to generate concise summaries of news articles. To use this feature:

1. Set up your Azure OpenAI credentials in the `.env` file
2. In the frontend, check the "Generate AI summaries for articles" option before fetching news
3. View AI-generated summaries alongside article content

## Testing

Run tests with:
```
poetry run pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
