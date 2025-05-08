import logging
import uuid
from datetime import datetime

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db.crud import (add_bookmark, add_user_channel,
                         create_or_update_article, delete_channel,
                         get_article_by_url, get_articles, get_channel,
                         get_user_bookmarks, get_user_channels, is_bookmarked,
                         remove_bookmark, update_channel)
from app.db.models import Bookmark, NewsArticle, User, UserChannels

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Sample data for testing
@pytest.fixture
def sample_article_data():
    url_uuid = uuid.uuid4()
    logger.debug(f"Creating sample article data with UUID: {url_uuid}")
    return {
        "title": "Test Article",
        "content": "This is test content",
        "url": f"https://example.com/test-{url_uuid}",
        "source": "test_source",
        "published_date": datetime.now(),
        "ai_summary": "This is an AI summary",
        "category": "Technology",
    }


@pytest.fixture
def sample_user(test_db: Session):
    # Create a test user
    username = f"testuser_{uuid.uuid4()}"
    email = f"testuser_{uuid.uuid4()}@example.com"
    logger.debug(f"Creating sample user with username: {username}, email: {email}")

    user = User(
        username=username, email=email, hashed_password="hashed_password_for_testing"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    logger.debug(f"Created user with ID: {user.id}")
    return user


def test_create_and_get_article_by_url(test_db: Session, sample_article_data):
    """Test creating an article and retrieving it by URL."""
    logger.debug("Starting test_create_and_get_article_by_url")

    # Log database info
    try:
        inspector = inspect(test_db.bind)
        tables = inspector.get_table_names()
        logger.debug(f"Database tables: {tables}")
        for table in tables:
            columns = [col["name"] for col in inspector.get_columns(table)]
            logger.debug(f"Table {table} columns: {columns}")
    except Exception as e:
        logger.error(f"Error inspecting database: {str(e)}")

    # Create article
    logger.debug(f"Creating article with URL: {sample_article_data['url']}")
    created_article = create_or_update_article(test_db, sample_article_data)
    logger.debug(f"Created article with ID: {created_article.id}")

    # Get by URL
    retrieved_article = get_article_by_url(test_db, sample_article_data["url"])
    logger.debug(f"Retrieved article: {retrieved_article is not None}")

    # Assertions
    assert retrieved_article is not None
    assert retrieved_article.id == created_article.id
    assert retrieved_article.title == sample_article_data["title"]
    assert retrieved_article.content == sample_article_data["content"]
    assert retrieved_article.url == sample_article_data["url"]
    assert retrieved_article.source == sample_article_data["source"]
    assert retrieved_article.ai_summary == sample_article_data["ai_summary"]
    assert retrieved_article.category == sample_article_data["category"]
    logger.debug("Article creation and retrieval test passed")


def test_update_existing_article(test_db: Session, sample_article_data):
    """Test updating an existing article."""
    # First create the article
    article = create_or_update_article(test_db, sample_article_data)

    # Update the article
    updated_data = sample_article_data.copy()
    updated_data["title"] = "Updated Title"
    updated_data["ai_summary"] = "Updated AI summary"

    updated_article = create_or_update_article(test_db, updated_data)

    # Get the article from the database
    retrieved_article = get_article_by_url(test_db, sample_article_data["url"])

    # Assertions
    assert retrieved_article.id == article.id  # Same article
    assert retrieved_article.title == "Updated Title"
    assert retrieved_article.ai_summary == "Updated AI summary"
    assert retrieved_article.url == sample_article_data["url"]  # URL unchanged


def test_get_articles_with_filters(test_db: Session):
    """Test retrieving articles with source and category filters."""
    logger.debug("Starting test_get_articles_with_filters")

    # Create test articles with different sources and categories
    uuid1 = uuid.uuid4()
    uuid2 = uuid.uuid4()
    uuid3 = uuid.uuid4()

    article1 = {
        "title": "Technology News",
        "content": "Technology content",
        "url": f"https://example.com/tech-{uuid1}",
        "source": "tech_source",
        "published_date": datetime.now(),
        "category": "Technology",
    }

    article2 = {
        "title": "Science News",
        "content": "Science content",
        "url": f"https://example.com/science-{uuid2}",
        "source": "science_source",
        "published_date": datetime.now(),
        "category": "Science",
    }

    article3 = {
        "title": "More Technology",
        "content": "More tech content",
        "url": f"https://example.com/more-tech-{uuid3}",
        "source": "tech_source",
        "published_date": datetime.now(),
        "category": "Technology",
    }

    logger.debug("Creating test articles for filtering")
    a1 = create_or_update_article(test_db, article1)
    a2 = create_or_update_article(test_db, article2)
    a3 = create_or_update_article(test_db, article3)
    logger.debug(f"Created articles with IDs: {a1.id}, {a2.id}, {a3.id}")

    # Test filter by source
    logger.debug("Getting articles filtered by source='tech_source'")
    tech_articles = get_articles(test_db, source="tech_source")
    logger.debug(f"Retrieved {len(tech_articles)} tech articles")

    if tech_articles:
        logger.debug(f"Article sources: {[a.source for a in tech_articles]}")

    assert len(tech_articles) == 2
    assert all(a.source == "tech_source" for a in tech_articles)

    # Test filter by category
    logger.debug("Getting articles filtered by category='Science'")
    science_articles = get_articles(test_db, category="Science")
    logger.debug(f"Retrieved {len(science_articles)} science articles")

    if science_articles:
        logger.debug(f"Article categories: {[a.category for a in science_articles]}")

    assert len(science_articles) == 1
    assert science_articles[0].category == "Science"

    # Test filter by both source and category
    logger.debug(
        "Getting articles filtered by source='tech_source' and category='Technology'"
    )
    tech_category_articles = get_articles(
        test_db, source="tech_source", category="Technology"
    )
    logger.debug(f"Retrieved {len(tech_category_articles)} tech category articles")

    if tech_category_articles:
        logger.debug(
            f"Article sources and categories: {[(a.source, a.category) for a in tech_category_articles]}"
        )

    assert len(tech_category_articles) == 2
    assert all(
        a.source == "tech_source" and a.category == "Technology"
        for a in tech_category_articles
    )

    logger.debug("Article filtering test passed")


def test_user_channel_operations(test_db: Session, sample_user):
    """Test operations for managing user channels."""
    logger.debug("Starting test_user_channel_operations")

    user_id = str(sample_user.id)
    logger.debug(f"User ID: {user_id}, Type: {type(user_id)}")

    # Log UserChannels table schema
    try:
        inspector = inspect(test_db.bind)
        columns = [col for col in inspector.get_columns("user_channels")]
        logger.debug(f"UserChannels table columns: {columns}")

        # Check column types
        for col in columns:
            if col["name"] == "id":
                logger.debug(f"UserChannels.id column type: {col['type']}")
    except Exception as e:
        logger.error(f"Error inspecting UserChannels table: {str(e)}")

    # Add channels
    logger.debug(f"Adding channel @channel1 for user {user_id}")
    channel1 = add_user_channel(test_db, user_id, "@channel1")
    logger.debug(f"Added channel with ID: {channel1.id}, Type: {type(channel1.id)}")

    logger.debug(f"Adding channel @channel2 for user {user_id}")
    channel2 = add_user_channel(test_db, user_id, "@channel2")
    logger.debug(f"Added channel with ID: {channel2.id}, Type: {type(channel2.id)}")

    # Get all channels
    logger.debug(f"Retrieving channels for user {user_id}")
    channels = get_user_channels(test_db, user_id)
    logger.debug(f"Retrieved {len(channels)} channels")

    assert len(channels) == 2
    channel_aliases = [c.channel_alias for c in channels]
    logger.debug(f"Channel aliases: {channel_aliases}")
    assert "@channel1" in channel_aliases
    assert "@channel2" in channel_aliases

    # Get specific channel
    # Convert UUID object to string using the standard UUID string representation
    channel_id = str(channel1.id)
    logger.debug(
        f"Retrieving specific channel with ID: {channel_id}, Type: {type(channel_id)}"
    )

    # Using SQLAlchemy directly with raw SQL to work around UUID issues
    try:
        result = test_db.execute(
            text("SELECT * FROM user_channels WHERE id = :id"), {"id": str(channel1.id)}
        ).fetchall()
        logger.debug(f"Raw SQL result for channel {channel_id}: {result}")

        # Now use the CRUD function for assertion
        retrieved_channel = get_channel(
            test_db, channel1.id
        )  # Pass the UUID object directly
        logger.debug(f"Retrieved channel: {retrieved_channel is not None}")
        if retrieved_channel:
            logger.debug(f"Channel alias: {retrieved_channel.channel_alias}")

        assert retrieved_channel is not None
        assert retrieved_channel.channel_alias == "@channel1"
    except Exception as e:
        logger.error(f"Error retrieving channel: {str(e)}")
        raise

    # Update channel
    logger.debug(f"Updating channel {channel_id} to @updated_channel")
    try:
        updated_channel = update_channel(
            test_db, channel1.id, "@updated_channel"
        )  # Pass the UUID object directly
        logger.debug(f"Updated channel: {updated_channel is not None}")
        if updated_channel:
            logger.debug(f"Updated channel alias: {updated_channel.channel_alias}")

        assert updated_channel.channel_alias == "@updated_channel"
    except Exception as e:
        logger.error(f"Error updating channel: {str(e)}")
        raise

    # Delete channel
    logger.debug(f"Deleting channel {channel_id}")
    try:
        delete_channel(test_db, channel1.id)  # Pass the UUID object directly
        logger.debug("Channel deleted")
    except Exception as e:
        logger.error(f"Error deleting channel: {str(e)}")
        raise

    remaining_channels = get_user_channels(test_db, user_id)
    logger.debug(f"Remaining channels count: {len(remaining_channels)}")
    if remaining_channels:
        logger.debug(
            f"Remaining channel aliases: {[c.channel_alias for c in remaining_channels]}"
        )

    assert len(remaining_channels) == 1
    assert remaining_channels[0].channel_alias == "@channel2"
    logger.debug("User channel operations test completed")


def test_bookmark_operations(test_db: Session, sample_user, sample_article_data):
    """Test bookmark operations."""
    user_id = str(sample_user.id)

    # Create a test article
    article = create_or_update_article(test_db, sample_article_data)
    article_id = article.id

    # Add bookmark
    bookmark = add_bookmark(test_db, user_id, article_id)
    assert bookmark is not None
    assert bookmark.user_id == user_id
    assert bookmark.article_id == article_id

    # Check if bookmarked
    assert is_bookmarked(test_db, user_id, article_id)

    # Get user bookmarks
    user_bookmarks = get_user_bookmarks(test_db, user_id)
    assert len(user_bookmarks) == 1
    assert user_bookmarks[0].article_id == article_id

    # Remove bookmark
    removed = remove_bookmark(test_db, user_id, article_id)
    assert removed is True

    # Verify bookmark is removed
    assert not is_bookmarked(test_db, user_id, article_id)
    assert len(get_user_bookmarks(test_db, user_id)) == 0

    # Try to remove non-existent bookmark
    non_existent_removal = remove_bookmark(test_db, user_id, 9999)
    assert non_existent_removal is False


def test_create_article_missing_url(test_db: Session):
    """Test creating an article without URL raises ValueError."""
    logger.debug("Starting test_create_article_missing_url")

    invalid_data = {
        "title": "Invalid Article",
        "content": "Content without URL",
        # URL is missing
    }
    logger.debug(f"Attempting to create article with invalid data: {invalid_data}")

    try:
        with pytest.raises(ValueError, match="Article data must contain URL"):
            create_or_update_article(test_db, invalid_data)
        logger.debug("Test passed: ValueError raised as expected")
    except Exception as e:
        logger.error(f"Unexpected error in test: {str(e)}")
        raise
