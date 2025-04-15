"""
Unit tests for CRUD operations.
"""
import pytest

from app.db import crud
from app.db.models import NewsArticle


def test_get_article(test_db, sample_articles):
    """Test getting an article by ID."""
    article = crud.get_article(test_db, article_id=sample_articles[0].id)
    assert article is not None
    assert article.title == "Test Article 1"
    assert article.source == "Test Source"


def test_get_article_not_found(test_db):
    """Test getting an article that doesn't exist."""
    article = crud.get_article(test_db, article_id=999)
    assert article is None


def test_get_article_by_url(test_db, sample_articles):
    """Test getting an article by URL."""
    article = crud.get_article_by_url(test_db, url="http://example.com/article1")
    assert article is not None
    assert article.title == "Test Article 1"


def test_get_articles(test_db, sample_articles):
    """Test getting multiple articles."""
    articles = crud.get_articles(test_db)
    assert len(articles) == 2
    assert articles[0].title in ["Test Article 1", "Test Article 2"]
    assert articles[1].title in ["Test Article 1", "Test Article 2"]


def test_get_articles_with_source_filter(test_db, sample_articles):
    """Test getting articles filtered by source."""
    articles = crud.get_articles(test_db, source="Test Source")
    assert len(articles) == 2
    
    articles = crud.get_articles(test_db, source="Non-existent Source")
    assert len(articles) == 0


def test_get_articles_with_category_filter(test_db, sample_articles):
    """Test getting articles filtered by category."""
    articles = crud.get_articles(test_db, category="politics")
    assert len(articles) == 1
    assert articles[0].title == "Test Article 1"
    
    articles = crud.get_articles(test_db, category="technology")
    assert len(articles) == 1
    assert articles[0].title == "Test Article 2" 