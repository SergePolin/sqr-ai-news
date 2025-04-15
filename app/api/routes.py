from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db import crud
from app.schemas.news import NewsArticle

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/articles/", response_model=List[NewsArticle])
def read_articles(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve news articles with optional filtering.
    """
    articles = crud.get_articles(db, skip=skip, limit=limit, source=source, category=category)
    return articles


@router.get("/articles/{article_id}", response_model=NewsArticle)
def read_article(article_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific news article by ID.
    """
    db_article = crud.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return db_article 