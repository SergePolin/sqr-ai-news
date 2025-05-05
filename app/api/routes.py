from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db import crud
from app.schemas.news import NewsArticle
from app.core.dependencies import get_current_active_user
from app.db.models import User

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/articles/", response_model=List[NewsArticle])
def read_articles(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve news articles with optional filtering.
    
    Parameters:
    - skip: Number of articles to skip
    - limit: Maximum number of articles to return
    - source: Filter by news source
    - category: Filter by article category
    """
    articles = crud.get_articles(db, skip=skip, limit=limit, source=source, category=category)
    return articles


@router.get("/articles/{article_id}", response_model=NewsArticle)
def read_article(
    article_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific news article by ID.
    """
    db_article = crud.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return db_article


@router.get("/sources/")
def get_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a list of all available news sources.
    """
    # Query all distinct sources from the database
    sources = db.query(crud.NewsArticle.source).distinct().all()
    return [source[0] for source in sources if source[0]] 