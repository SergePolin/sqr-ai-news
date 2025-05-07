from sqlalchemy.orm import Session
# from sqlalchemy import and_
from typing import List, Optional, Dict, Any
# from datetime import datetime

from app.db.models import NewsArticle, UserChannels, User, Bookmark
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate


def get_articles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None
) -> List[NewsArticle]:
    """
    Get articles with optional filtering by source and category.
    """
    query = db.query(NewsArticle)

    if source:
        query = query.filter(NewsArticle.source == source)

    if category:
        query = query.filter(NewsArticle.category == category)

    return query.offset(skip).limit(limit).all()


def get_article(db: Session, article_id: int) -> Optional[NewsArticle]:
    """
    Get a specific article by ID.
    """
    return db.query(NewsArticle).filter(NewsArticle.id == article_id).first()


def get_article_by_url(db: Session, url: str) -> Optional[NewsArticle]:
    """
    Get a news article by its URL.
    """
    return db.query(NewsArticle).filter(NewsArticle.url == url).first()


def create_or_update_article(
    db: Session,
    article_data: Dict[str, Any]
) -> NewsArticle:
    """
    Create a new article or update if it already exists (by URL).

    Args:
        db: Database session
        article_data: Dictionary containing article data

    Returns:
        Created or updated NewsArticle object
    """
    # Check if article already exists
    if 'url' not in article_data:
        raise ValueError("Article data must contain URL")

    existing_article = get_article_by_url(db, article_data['url'])

    if existing_article:
        # Update existing article
        for key, value in article_data.items():
            if hasattr(existing_article, key) and key != 'id':
                setattr(existing_article, key, value)

        db.commit()
        db.refresh(existing_article)
        return existing_article
    else:
        # Create new article
        new_article = NewsArticle(**article_data)
        db.add(new_article)
        db.commit()
        db.refresh(new_article)
        return new_article


def add_user_channel(db: Session, user_id: str, channel_alias: str):
    """
    Add a channel for a user.
    """
    db_channel = UserChannels(user_id=user_id, channel_alias=channel_alias)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel


def get_user_channels(db: Session, user_id: str):
    """
    Get all channels for a user.
    """
    return db.query(UserChannels).filter(UserChannels.user_id == user_id).all()


# Read - Получение конкретной подписки
def get_channel(db: Session, channel_id: str):
    return db.query(UserChannels).filter(UserChannels.id == channel_id).first()


# Update - Обновление подписки
def update_channel(db: Session, channel_id: str, new_channel_alias: str):
    db_channel = db.query(UserChannels).filter(
        UserChannels.id == channel_id).first()
    if db_channel:
        db_channel.channel_alias = new_channel_alias
        db.commit()
        db.refresh(db_channel)
    return db_channel


# Delete - Удаление подписки
def delete_channel(db: Session, channel_id: str):
    db_channel = db.query(UserChannels).filter(
        UserChannels.id == channel_id).first()
    if db_channel:
        db.delete(db_channel)
        db.commit()
    return db_channel


# User-related operations

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(
    db: Session,
    username: str, password: str
) -> Optional[User]:
    """
    Authenticate a user by username and password.
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def add_bookmark(db: Session, user_id: str, article_id: int) -> Bookmark:
    bookmark = Bookmark(user_id=user_id, article_id=article_id)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


def remove_bookmark(db: Session, user_id: str, article_id: int) -> bool:
    bookmark = db.query(Bookmark).filter_by(
        user_id=user_id, article_id=article_id).first()
    if bookmark:
        db.delete(bookmark)
        db.commit()
        return True
    return False


def get_user_bookmarks(db: Session, user_id: str) -> list[Bookmark]:
    return db.query(Bookmark).filter_by(user_id=user_id).all()


def is_bookmarked(db: Session, user_id: str, article_id: int) -> bool:
    return (
        db.query(Bookmark)
        .filter_by(user_id=user_id, article_id=article_id)
        .first()
        is not None
    )
