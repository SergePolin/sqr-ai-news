"""
Integration tests for database operations.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import NewsArticle


def test_create_article(test_db):
    """Test creating a new article in the database."""
    # Create a new article
    article = NewsArticle(
        title="Integration Test Article",
        content="Test content for integration test",
        url="http://example.com/integration-test",
        source="Integration Test Source",
        category="test",
    )
    
    # Add to database
    test_db.add(article)
    test_db.commit()
    test_db.refresh(article)
    
    # Retrieve and verify
    retrieved_article = test_db.query(NewsArticle).filter(NewsArticle.id == article.id).first()
    assert retrieved_article is not None
    assert retrieved_article.title == "Integration Test Article"
    assert retrieved_article.source == "Integration Test Source"
    
    # Clean up
    test_db.delete(article)
    test_db.commit()


def test_unique_url_constraint(test_db):
    """Test that the URL must be unique."""
    # Create a new article
    article1 = NewsArticle(
        title="First Article",
        content="First content",
        url="http://example.com/duplicate-url",
        source="Test Source",
        category="test",
    )
    
    test_db.add(article1)
    test_db.commit()
    
    # Try to create another article with the same URL
    article2 = NewsArticle(
        title="Second Article",
        content="Second content",
        url="http://example.com/duplicate-url",  # Same URL as article1
        source="Test Source",
        category="test",
    )
    
    test_db.add(article2)
    
    # This should raise an IntegrityError due to the unique constraint on URL
    with pytest.raises(IntegrityError):
        test_db.commit()
    
    # Rollback and clean up
    test_db.rollback()
    test_db.delete(article1)
    test_db.commit()


def test_article_update(test_db):
    """Test updating an article in the database."""
    # Create a new article
    article = NewsArticle(
        title="Article to Update",
        content="Initial content",
        url="http://example.com/update-test",
        source="Test Source",
        category="initial",
    )
    
    test_db.add(article)
    test_db.commit()
    test_db.refresh(article)
    
    # Update the article
    article.title = "Updated Title"
    article.content = "Updated content"
    article.category = "updated"
    test_db.commit()
    
    # Retrieve and verify
    updated_article = test_db.query(NewsArticle).filter(NewsArticle.id == article.id).first()
    assert updated_article.title == "Updated Title"
    assert updated_article.content == "Updated content"
    assert updated_article.category == "updated"
    
    # Clean up
    test_db.delete(article)
    test_db.commit() 