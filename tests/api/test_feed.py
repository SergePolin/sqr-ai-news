# import json  # Unused import
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import text

# from sqlalchemy.orm import Session  # Unused import
from app.db.crud import create_or_update_article, get_user_by_username

# from app.db.models import User, UserChannels  # Unused import
from app.db.models import NewsArticle
from app.main import app

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = TestClient(app)


@pytest.fixture(scope="function")
def clean_user_channels(test_db):
    """Clean user_channels table before and after tests."""
    test_db.execute(text("DELETE FROM user_channels"))
    test_db.commit()
    yield
    test_db.execute(text("DELETE FROM user_channels"))
    test_db.commit()


@pytest.fixture(scope="function")
def clean_articles(test_db):
    """Clean news_articles table before and after tests."""
    test_db.execute(text("DELETE FROM news_articles"))
    test_db.commit()
    yield
    test_db.execute(text("DELETE FROM news_articles"))
    test_db.commit()


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user for authentication."""
    # Use a unique username to avoid conflicts
    unique_id = uuid4().hex[:8]
    username = f"feed_test_user_{unique_id}"
    email = f"{username}@example.com"
    password = "password123"

    # Create user via API
    _ = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )

    # Get token
    token_response = client.post(
        "/auth/login", data={"username": username, "password": password}
    )
    token = token_response.json()["access_token"]

    # Get user object from database
    user = get_user_by_username(test_db, username)

    return {"user": user, "token": token, "username": username}


def test_create_channel(test_user, clean_user_channels):
    """Test creating a new channel."""
    token = test_user["token"]

    channel_data = {"Channel_alias": "@test_channel"}

    with patch("app.api.feed.process_channel_articles"):
        response = client.post(
            "/feed/", json=channel_data, headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["channel_alias"] == "@test_channel"
    assert "id" in data


def test_get_channels_with_articles_empty(
    test_user, clean_user_channels, clean_articles
):
    """Test getting channels when no channels are added."""
    token = test_user["token"]

    response = client.get("/feed/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_get_channels_with_articles(
    test_user, test_db, clean_user_channels, clean_articles
):
    """Test getting channels with articles."""
    token = test_user["token"]

    # First create a channel
    channel_data = {"Channel_alias": "@test_channel"}

    with patch("app.api.feed.process_channel_articles"):
        response = client.post(
            "/feed/", json=channel_data, headers={"Authorization": f"Bearer {token}"}
        )

    # Create test article with proper datetime object
    article_data = {
        "title": "Test Article",
        "content": "This is a test article",
        "url": "https://example.com/test",
        "source": "@test_channel",
        "published_date": datetime(
            2025, 1, 1, 12, 0, 0
        ),  # Use datetime object instead of string
    }
    article = create_or_update_article(test_db, article_data)

    # Use patch to mock the response for get_articles
    with patch("app.api.feed.get_articles") as mock_get_articles:
        with patch("app.api.feed.get_user_channels") as mock_get_channels:
            # Create a mock channel
            mock_channel = MagicMock()
            mock_channel.id = uuid4()
            mock_channel.channel_alias = "@test_channel"
            mock_get_channels.return_value = [mock_channel]

            # Create a mock article list
            mock_get_articles.return_value = [article]

            # Get channels
            response = client.get(
                "/feed/", headers={"Authorization": f"Bearer {token}"}
            )

    assert response.status_code == 200
    data = response.json()

    # Print detailed info for debugging
    print(f"Response data: {data}")

    assert len(data) == 1
    assert data[0]["channel_alias"] == "@test_channel"
    assert len(data[0]["articles"]) == 1
    assert data[0]["articles"][0]["title"] == "Test Article"


def test_update_all_channels(test_user, test_db, clean_user_channels):
    """Test updating all channels."""
    token = test_user["token"]

    # First create a channel
    channel_data = {"Channel_alias": "@test_channel"}

    with patch("app.api.feed.process_channel_articles"):
        client.post(
            "/feed/", json=channel_data, headers={"Authorization": f"Bearer {token}"}
        )

    # Test update endpoint
    with patch("app.api.feed.process_channel_articles") as mock_process:
        response = client.post(
            "/feed/update", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    assert "message" in response.json()
    assert "Update started" in response.json()["message"]
    assert mock_process.call_count >= 1


def test_update_all_channels_no_channels(test_user, clean_user_channels):
    """Test updating when no channels exist."""
    token = test_user["token"]

    response = client.post("/feed/update", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert "No channels found" in response.json()["detail"]


@patch("app.api.feed.requests.get")
@patch("app.api.feed.feedparser.parse")
@patch("app.api.feed.generate_article_summary")
@patch("app.api.feed.generate_article_category")
@patch("app.api.feed.BeautifulSoup")
def test_process_channel_articles(
    mock_bs, mock_category, mock_summary, mock_parse, mock_get, test_db, clean_articles
):
    """Test the process_channel_articles function directly."""
    # Mock responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Mock feedparser
    mock_feed = MagicMock()
    mock_entry = {
        "title": "Test Article",
        "link": "https://example.com/test",
        "description": "<p>Test content</p>",
        "published": "Mon, 01 Jan 2025 12:00:00 GMT",
    }
    mock_feed.entries = [mock_entry]
    mock_parse.return_value = mock_feed

    # Mock BeautifulSoup
    mock_soup = MagicMock()
    mock_soup.get_text.return_value = (
        "This is a long text that is more than 50 characters to pass the length check"
    )
    mock_bs.return_value = mock_soup

    # Mock AI functions
    mock_summary.return_value = "This is a summary"
    mock_category.return_value = "Technology"

    from app.api.feed import process_channel_articles

    # Call function directly
    process_channel_articles("@test_channel", test_db, max_articles=1)

    # Check database
    articles = test_db.query(NewsArticle).all()
    assert len(articles) == 1
    assert articles[0].title == "Test Article"
    assert articles[0].source == "@test_channel"
    assert articles[0].ai_summary == "This is a summary"
    assert articles[0].category == "Technology"


@patch("app.api.feed.requests.get")
def test_process_channel_articles_request_error(mock_get, test_db, clean_articles):
    """Test handling of request errors in process_channel_articles."""
    # Mock network error
    mock_get.side_effect = requests.RequestException("Network error")

    from app.api.feed import process_channel_articles

    # Call function directly with small retry count for testing
    process_channel_articles("@test_channel", test_db, retry_count=1)

    # Check no articles were added
    articles = test_db.query(NewsArticle).all()
    assert len(articles) == 0


@patch("app.api.feed.requests.get")
def test_process_channel_articles_rate_limit(mock_get, test_db, clean_articles):
    """Test handling of rate limits in process_channel_articles."""
    # First response is rate limited, second is successful
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "1"}  # Quick retry for testing

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    # Empty feed to keep test simple
    mock_response_200.content = b'{"feed": {}, "entries": []}'

    mock_get.side_effect = [mock_response_429, mock_response_200]

    from app.api.feed import process_channel_articles

    # Patch sleep to avoid waiting in tests
    with patch("app.api.feed.time.sleep"):
        process_channel_articles("@test_channel", test_db)

    # We're just testing it didn't raise an exception
    assert True


@patch("app.api.feed.is_bookmarked")
def test_add_article_bookmark(mock_is_bookmarked, test_user, test_db, clean_articles):
    """Test adding an article to bookmarks."""
    token = test_user["token"]
    mock_is_bookmarked.return_value = False

    # Create test article
    article_data = {
        "title": "Test Article",
        "content": "This is a test article",
        "url": "https://example.com/test",
        "source": "@test_channel",
        "published_date": datetime(2025, 1, 1, 12, 0, 0),
    }
    article = create_or_update_article(test_db, article_data)

    # Add bookmark
    response = client.post(
        f"/feed/bookmarks/{article.id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["article_id"] == article.id


@patch("app.api.feed.remove_bookmark")
def test_delete_article_bookmark(
    mock_remove_bookmark, test_user, test_db, clean_articles
):
    """Test removing an article from bookmarks."""
    token = test_user["token"]
    mock_remove_bookmark.return_value = True

    # Create test article
    article_data = {
        "title": "Test Article",
        "content": "This is a test article",
        "url": "https://example.com/test",
        "source": "@test_channel",
        "published_date": datetime(2025, 1, 1, 12, 0, 0),
    }
    article = create_or_update_article(test_db, article_data)

    # Delete bookmark
    response = client.delete(
        f"/feed/bookmarks/{article.id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204
    mock_remove_bookmark.assert_called_once()


@patch("app.api.feed.get_user_bookmarks")
@patch("app.db.crud.get_article")
def test_list_user_bookmarks(
    mock_get_article, mock_get_user_bookmarks, test_user, test_db, clean_articles
):
    """Test listing user bookmarks."""
    token = test_user["token"]

    # Create test article
    article_data = {
        "title": "Test Article",
        "content": "This is a test article",
        "url": "https://example.com/test",
        "source": "@test_channel",
        "published_date": datetime(2025, 1, 1, 12, 0, 0),
    }
    article = create_or_update_article(test_db, article_data)

    # Mock bookmarks
    mock_bookmark = MagicMock()
    mock_bookmark.article_id = article.id
    mock_get_user_bookmarks.return_value = [mock_bookmark]

    # Mock get_article
    mock_get_article.return_value = article

    # Get bookmarks
    response = client.get(
        "/feed/bookmarks", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    print(f"Test article: {article.title}, Response: {data}")
    assert len(data) == 1


def test_get_news_channel_not_found(client, mock_db_session):
    """Test getting news when the channel doesn't exist."""
    # Mock the get_channel function to return None
    with patch("app.db.crud.get_channel", return_value=None):
        # Call the API
        response = client.get("/api/feed/news/invalid-channel")
        # Check response
        assert response.status_code == 404  # Adding assertion for unused variable


class MockChannel:
    """Mock channel for testing."""

    def __init__(self):
        self.id = 123
        self.channel_alias = "@test_channel"


def test_process_new_articles(client, mock_db_session):
    """Test processing new articles."""
    # Mock get_channel
    with patch("app.db.crud.get_channel", return_value=MockChannel()):
        # Mock get_user_channel to return True
        with patch("app.db.crud.get_user_channel", return_value=True):
            # Mock process_articles
            with patch(
                "app.api.feed.process_channel_articles", return_value=None
            ) as mock_process:
                # Call the API
                response = client.post("/api/feed/process/123")
                # Check response and verify mock was called
                assert response.status_code == 200
                mock_process.assert_called_once()  # Use mock to avoid unused variable
