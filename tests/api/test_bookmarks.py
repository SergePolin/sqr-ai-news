import logging
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.crud import create_or_update_article, get_user_by_username, is_bookmarked
from app.main import app

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = TestClient(app)


@pytest.fixture(scope="function")
def clean_db(test_db):
    """Clean the articles and bookmarks tables before tests to avoid conflicts."""
    # Delete all existing bookmarks and articles
    test_db.execute(text("DELETE FROM bookmarks"))
    test_db.execute(text("DELETE FROM news_articles"))
    test_db.commit()
    yield
    # Clean up after test
    test_db.execute(text("DELETE FROM bookmarks"))
    test_db.execute(text("DELETE FROM news_articles"))
    test_db.commit()


def create_test_article(test_db):
    """Helper to create a test article."""
    unique_id = uuid4().hex[:8]
    article_data = {
        "title": f"Test Article {unique_id}",
        "content": "This is a test article for bookmarking.",
        "url": f"https://example.com/test-{unique_id}",
        "source": "test_source",
        "published_date": datetime.now(),
    }
    logger.debug(f"Creating test article with data: {article_data}")

    try:
        article = create_or_update_article(test_db, article_data)
        logger.debug(f"Created article with ID: {article.id}")
        return article
    except Exception as e:
        logger.error(f"Error creating test article: {str(e)}")
        raise


def get_auth_token(username="bookmark_user", password="password123"):
    """Helper to get authentication token."""
    # Add a unique suffix to username to avoid conflicts
    unique_id = uuid4().hex[:8]
    username = f"{username}_{unique_id}"

    # Register user if needed
    register_data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
    }
    logger.debug(f"Registering user for auth token: {register_data}")

    register_response = client.post("/auth/register", json=register_data)
    logger.debug(f"Registration response status: {register_response.status_code}")
    logger.debug(f"Registration response body: {register_response.text}")

    # Get token
    login_data = {"username": username, "password": password}
    logger.debug(f"Logging in to get auth token: {login_data}")

    login_response = client.post("/auth/login", data=login_data)
    logger.debug(f"Login response status: {login_response.status_code}")
    logger.debug(f"Login response body: {login_response.text}")

    token = login_response.json()["access_token"]
    logger.debug(f"Retrieved token (first 15 chars): {token[:15]}...")
    return username, token


def test_add_bookmark(test_db: Session, clean_db):
    """Test adding an article to bookmarks."""
    # Create test article
    logger.debug("Starting test_add_bookmark")
    article = create_test_article(test_db)
    print(f"Debug - Created test article ID: {article.id}")

    # Get auth token
    username, token = get_auth_token()
    print(f"Debug - Got token for user {username}, token prefix: {token[:10]}...")

    # Add bookmark
    logger.debug(f"Adding bookmark for article ID: {article.id}")
    auth_header = {"Authorization": f"Bearer {token}"}
    print(f"Debug - Auth header: {auth_header}")
    
    endpoint = f"/feed/bookmarks/{article.id}"
    print(f"Debug - Endpoint: {endpoint}")
    
    response = client.post(endpoint, headers=auth_header)
    
    logger.debug(f"Add bookmark response status: {response.status_code}")
    logger.debug(f"Add bookmark response body: {response.text}")
    print(f"Debug - Response status: {response.status_code}")
    print(f"Debug - Response body: {response.text}")

    assert response.status_code == 201
    data = response.json()
    assert data["article_id"] == article.id

    # Verify bookmark exists in database
    user = get_user_by_username(test_db, username)
    logger.debug(f"User retrieved from database: {user is not None}")
    if user:
        logger.debug(f"User ID: {user.id}, Username: {user.username}")
        # Check bookmarks
        is_marked = is_bookmarked(test_db, str(user.id), article.id)
        logger.debug(f"Article is bookmarked: {is_marked}")
        assert is_marked


def test_add_bookmark_nonexistent_article(test_db: Session, clean_db):
    """Test adding a non-existent article to bookmarks."""
    logger.debug("Starting test_add_bookmark_nonexistent_article")

    # Get auth token
    username, token = get_auth_token()

    # Try to add bookmark for non-existent article
    non_existent_id = 99999
    logger.debug(f"Adding bookmark for non-existent article ID: {non_existent_id}")

    response = client.post(
        f"/feed/bookmarks/{non_existent_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    logger.debug(f"Add bookmark response status: {response.status_code}")
    logger.debug(f"Add bookmark response body: {response.text}")

    assert response.status_code == 404
    assert "Article not found" in response.json()["detail"]


def test_add_bookmark_duplicate(test_db: Session, clean_db):
    """Test adding the same article to bookmarks twice."""
    # Create test article
    article = create_test_article(test_db)

    # Get auth token
    username, token = get_auth_token()

    # Add bookmark first time
    response = client.post(
        f"/feed/bookmarks/{article.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    # Add bookmark second time
    response = client.post(
        f"/feed/bookmarks/{article.id}", headers={"Authorization": f"Bearer {token}"}
    )
    # Should return 400 if already bookmarked
    assert response.status_code == 400
    assert "Article already bookmarked" in response.json()["detail"]


def test_delete_bookmark(test_db: Session, clean_db):
    """Test removing an article from bookmarks."""
    # Create test article
    article = create_test_article(test_db)

    # Get auth token
    username, token = get_auth_token()

    # Add bookmark
    add_response = client.post(
        f"/feed/bookmarks/{article.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert add_response.status_code == 201

    # Delete bookmark
    response = client.delete(
        f"/feed/bookmarks/{article.id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204

    # Verify bookmark is removed by trying to retrieve all bookmarks
    bookmarks_response = client.get(
        "/feed/bookmarks", headers={"Authorization": f"Bearer {token}"}
    )
    assert bookmarks_response.status_code == 200
    bookmarks = bookmarks_response.json()

    # Verify the article is not in bookmarks
    article_ids = [article["id"] for article in bookmarks]
    assert article.id not in article_ids


def test_delete_nonexistent_bookmark(test_db: Session, clean_db):
    """Test deleting a bookmark that doesn't exist."""
    # Create test article
    article = create_test_article(test_db)

    # Get auth token
    username, token = get_auth_token()

    # Delete bookmark that doesn't exist (article exists but not bookmarked)
    response = client.delete(
        f"/feed/bookmarks/{article.id}", headers={"Authorization": f"Bearer {token}"}
    )

    # Should return 204 (idempotent delete)
    assert response.status_code == 204


def test_list_bookmarks(test_db: Session, clean_db):
    """Test listing all bookmarks for a user."""
    logger.debug("Starting test_list_bookmarks")

    # Create test articles
    article1 = create_test_article(test_db)
    article2 = create_test_article(test_db)
    logger.debug(f"Created article IDs: {article1.id}, {article2.id}")

    # Get auth token
    username, token = get_auth_token()

    # Add bookmarks
    logger.debug(f"Adding first bookmark for article ID: {article1.id}")
    bookmark1_response = client.post(
        f"/feed/bookmarks/{article1.id}", headers={"Authorization": f"Bearer {token}"}
    )
    logger.debug(f"First bookmark response status: {bookmark1_response.status_code}")
    logger.debug(f"First bookmark response body: {bookmark1_response.text}")

    logger.debug(f"Adding second bookmark for article ID: {article2.id}")
    bookmark2_response = client.post(
        f"/feed/bookmarks/{article2.id}", headers={"Authorization": f"Bearer {token}"}
    )
    logger.debug(f"Second bookmark response status: {bookmark2_response.status_code}")
    logger.debug(f"Second bookmark response body: {bookmark2_response.text}")

    # List bookmarks
    logger.debug("Fetching bookmarks list")
    response = client.get(
        "/feed/bookmarks", headers={"Authorization": f"Bearer {token}"}
    )
    logger.debug(f"List bookmarks response status: {response.status_code}")
    logger.debug(
        f"List bookmarks response body: {response.text[:500]}..."
    )  # Truncated for large responses

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Verify article IDs are in bookmarks
    article_ids = [article["id"] for article in data]
    logger.debug(f"Bookmark article IDs: {article_ids}")
    assert article1.id in article_ids
    assert article2.id in article_ids
