from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.models import NewsArticle
from app.db import models


def get_article(db: Session, article_id: int) -> Optional[NewsArticle]:
    return db.query(NewsArticle).filter(NewsArticle.id == article_id).first()


def get_article_by_url(db: Session, url: str) -> Optional[NewsArticle]:
    return db.query(NewsArticle).filter(NewsArticle.url == url).first()


def get_articles(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None
) -> List[NewsArticle]:
    query = db.query(NewsArticle)
    
    if source:
        query = query.filter(NewsArticle.source == source)
    
    if category:
        query = query.filter(NewsArticle.category == category)
    
    return query.order_by(NewsArticle.published_date.desc()).offset(skip).limit(limit).all()


# Create - Создание новой подписки
def create_user_channel(db: Session, user_id: str, channel_alias: str):
    db_channel = models.UserChannels(
        user_id=user_id,
        channel_alias=channel_alias
    )
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel


# Read - Получение подписок пользователя
def get_user_channels(db: Session, user_id: str):
    return db.query(models.UserChannels).filter(models.UserChannels.user_id == user_id).all()


# Read - Получение конкретной подписки
def get_channel(db: Session, channel_id: str):
    return db.query(models.UserChannels).filter(models.UserChannels.id == channel_id).first()


# Update - Обновление подписки
def update_channel(db: Session, channel_id: str, new_channel_alias: str):
    db_channel = db.query(models.UserChannels).filter(models.UserChannels.id == channel_id).first()
    if db_channel:
        db_channel.channel_alias = new_channel_alias
        db.commit()
        db.refresh(db_channel)
    return db_channel


# Delete - Удаление подписки
def delete_channel(db: Session, channel_id: str):
    db_channel = db.query(models.UserChannels).filter(models.UserChannels.id == channel_id).first()
    if db_channel:
        db.delete(db_channel)
        db.commit()
    return db_channel 