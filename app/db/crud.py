from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.models import NewsArticle


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