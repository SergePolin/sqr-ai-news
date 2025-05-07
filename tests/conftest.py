"""
Common test fixtures for all tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from app.main import app
from app.db.database import Base, get_db
from app.db.models import NewsArticle


# Create in-memory test database
@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    os.remove("./test.db")


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine)
    test_db = TestSessionLocal()
    try:
        yield test_db
    finally:
        test_db.rollback()
        test_db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with the test database."""

    def _get_test_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_articles(test_db):
    """Create sample articles for testing."""
    articles = [
        NewsArticle(
            title="Test Article 1",
            content="Test content 1",
            url="http://example.com/article1",
            source="Test Source",
            category="politics",
            published_date=datetime.now(),
        ),
        NewsArticle(
            title="Test Article 2",
            content="Test content 2",
            url="http://example.com/article2",
            source="Test Source",
            category="technology",
            published_date=datetime.now(),
        ),
    ]

    for article in articles:
        test_db.add(article)
    test_db.commit()

    for article in articles:
        test_db.refresh(article)

    yield articles

    # Clean up
    for article in articles:
        test_db.delete(article)
    test_db.commit()


@pytest.fixture(scope="function")
def auth_token(client):
    """Register and log in a test user, return the JWT token."""
    username = "testuser"
    email = "testuser@example.com"
    password = "testpassword"
    # Register user (ignore if already exists)
    client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    # Login user
    response = client.post("/auth/login", data={
        "username": username,
        "password": password
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return token
