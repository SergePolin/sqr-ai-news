"""
Unit tests for CRUD operations.
"""

import pytest
from datetime import datetime
from app.db import crud
from app.db.models import NewsArticle


@pytest.fixture(scope="function")
def clean_articles_table(test_db):
    """Clean the articles table before tests."""
    # Delete all existing articles
    test_db.query(NewsArticle).delete()
    test_db.commit()
    yield
    # Clean up after test
    test_db.query(NewsArticle).delete()
    test_db.commit()


def test_get_article(test_db, clean_articles_table):
    """Test getting an article by ID."""
    # Create a test article
    article = NewsArticle(
        title="Test Article 1",
        content="Test content 1",
        url="http://example.com/article1-get-by-id",
        source="Test Source",
        category="politics",
        published_date=datetime.now(),
    )
    test_db.add(article)
    test_db.commit()
    test_db.refresh(article)

    # Run the test
    retrieved_article = crud.get_article(test_db, article_id=article.id)
    assert retrieved_article is not None
    assert retrieved_article.title == "Test Article 1"
    assert retrieved_article.source == "Test Source"


def test_get_article_not_found(test_db, clean_articles_table):
    """Test getting an article that doesn't exist."""
    article = crud.get_article(test_db, article_id=999)
    assert article is None


def test_get_article_by_url(test_db, clean_articles_table):
    """Test getting an article by URL."""
    # Create a test article
    article = NewsArticle(
        title="Test Article 1",
        content="Test content 1",
        url="http://example.com/article1-get-by-url",
        source="Test Source",
        category="politics",
        published_date=datetime.now(),
    )
    test_db.add(article)
    test_db.commit()

    # Run the test
    retrieved_article = crud.get_article_by_url(
        test_db, url="http://example.com/article1-get-by-url"
    )
    assert retrieved_article is not None
    assert retrieved_article.title == "Test Article 1"


def test_get_articles(test_db, clean_articles_table):
    """Test getting multiple articles."""
    # Create fresh test articles for this specific test
    articles_data = [
        NewsArticle(
            title="Test Article 1",
            content="Test content 1",
            url="http://example.com/article1-get-test",
            source="Test Source",
            category="politics",
            published_date=datetime.now(),
        ),
        NewsArticle(
            title="Test Article 2",
            content="Test content 2",
            url="http://example.com/article2-get-test",
            source="Test Source",
            category="technology",
            published_date=datetime.now(),
        ),
    ]

    # Add articles to test database
    for article in articles_data:
        test_db.add(article)
    test_db.commit()

    # Run the actual test
    articles = crud.get_articles(test_db)
    assert len(articles) == 2
    assert articles[0].title in ["Test Article 1", "Test Article 2"]
    assert articles[1].title in ["Test Article 1", "Test Article 2"]


def test_get_articles_with_source_filter(test_db, clean_articles_table):
    """Test getting articles filtered by source."""
    # Create fresh test articles for this specific test
    articles_data = [
        NewsArticle(
            title="Test Article 1",
            content="Test content 1",
            url="http://example.com/article1-source-test",
            source="Test Source",
            category="politics",
            published_date=datetime.now(),
        ),
        NewsArticle(
            title="Test Article 2",
            content="Test content 2",
            url="http://example.com/article2-source-test",
            source="Test Source",
            category="technology",
            published_date=datetime.now(),
        ),
    ]

    # Add articles to test database
    for article in articles_data:
        test_db.add(article)
    test_db.commit()

    # Run the actual test
    articles = crud.get_articles(test_db, source="Test Source")
    assert len(articles) == 2

    articles = crud.get_articles(test_db, source="Non-existent Source")
    assert len(articles) == 0


def test_get_articles_with_category_filter(test_db, clean_articles_table):
    """Test getting articles filtered by category."""
    # Create fresh test articles for this specific test
    articles_data = [
        NewsArticle(
            title="Test Article 1",
            content="Test content 1",
            url="http://example.com/article1-category-test",
            source="Test Source",
            category="politics",
            published_date=datetime.now(),
        ),
        NewsArticle(
            title="Test Article 2",
            content="Test content 2",
            url="http://example.com/article2-category-test",
            source="Test Source",
            category="technology",
            published_date=datetime.now(),
        ),
    ]

    # Add articles to test database
    for article in articles_data:
        test_db.add(article)
    test_db.commit()

    # Run the actual test
    articles = crud.get_articles(test_db, category="politics")
    assert len(articles) == 1
    assert articles[0].title == "Test Article 1"

    articles = crud.get_articles(test_db, category="technology")
    assert len(articles) == 1
    assert articles[0].title == "Test Article 2"
