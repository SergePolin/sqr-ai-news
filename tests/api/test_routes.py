"""
API tests for routes.
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_articles_endpoint(client, sample_articles):
    """Test getting all articles."""
    response = client.get("/api/news/articles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] in ["Test Article 1", "Test Article 2"]
    assert data[1]["title"] in ["Test Article 1", "Test Article 2"]


def test_get_articles_with_filter(client, sample_articles):
    """Test getting articles with filter."""
    response = client.get("/api/news/articles/?category=politics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Article 1"


def test_get_article_by_id(client, sample_articles):
    """Test getting an article by ID."""
    article_id = sample_articles[0].id
    response = client.get(f"/api/news/articles/{article_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Article 1"
    assert data["content"] == "Test content 1"
    assert data["url"] == "http://example.com/article1"


def test_get_article_not_found(client):
    """Test getting an article that doesn't exist."""
    response = client.get("/api/news/articles/999")
    assert response.status_code == 404
    assert "detail" in response.json() 