"""
Unit tests for Pydantic schema validation.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.news import NewsArticle, NewsArticleBase


def test_news_article_base_valid():
    """Test valid NewsArticleBase schema."""
    data = {
        "title": "Test Article",
        "content": "This is test content",
        "url": "http://example.com/test",
        "source": "Test Source",
        "published_date": datetime.now().isoformat(),
    }
    
    article = NewsArticleBase(**data)
    assert article.title == data["title"]
    assert article.content == data["content"]
    assert article.url == data["url"]
    assert article.source == data["source"]
    assert article.published_date is not None


def test_news_article_base_missing_required():
    """Test NewsArticleBase with missing required fields."""
    # Missing title
    data = {
        "content": "This is test content",
        "url": "http://example.com/test",
        "source": "Test Source",
    }
    
    with pytest.raises(ValidationError) as exc_info:
        NewsArticleBase(**data)
    
    errors = exc_info.value.errors()
    assert any(error["loc"][0] == "title" for error in errors)


def test_news_article_base_invalid_url():
    """Test NewsArticleBase with invalid URL."""
    data = {
        "title": "Test Article",
        "content": "This is test content",
        "url": "invalid-url",  # Invalid URL format
        "source": "Test Source",
        "published_date": datetime.now().isoformat(),
    }
    
    # This should not raise an error since we're not using HttpUrl type
    # In a real application you may want to validate URL format
    article = NewsArticleBase(**data)
    assert article.url == "invalid-url"


def test_news_article_model():
    """Test full NewsArticle model."""
    data = {
        "id": 1,
        "title": "Test Article",
        "content": "This is test content",
        "url": "http://example.com/test",
        "source": "Test Source",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "sentiment_score": 0.75,
        "category": "technology",
        "keywords": "test,article,technology",
        "published_date": datetime.now().isoformat(),
    }
    
    article = NewsArticle(**data)
    assert article.id == 1
    assert article.title == "Test Article"
    assert article.sentiment_score == 0.75
    assert article.category == "technology"


def test_news_article_optional_fields():
    """Test NewsArticle with optional fields omitted."""
    data = {
        "id": 1,
        "title": "Test Article",
        "content": "This is test content",
        "url": "http://example.com/test",
        "source": "Test Source",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "published_date": datetime.now().isoformat(),
    }
    
    article = NewsArticle(**data)
    assert article.id == 1
    assert article.sentiment_score is None
    assert article.category is None
    assert article.keywords is None 