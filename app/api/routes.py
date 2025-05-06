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
    - **skip** (query, optional): Number of articles to skip (pagination offset). Default: 0
    - **limit** (query, optional): Maximum number of articles to return. Default: 100
    - **source** (query, optional): Filter articles by news source
    - **category** (query, optional): Filter articles by article category
    
    Returns:
    - **List of NewsArticle**: Articles matching the filter criteria
    
    Raises:
    - **401 Unauthorized**: When user is not authenticated
    
    Example response:
    ```json
    [
      {
        "id": 1,
        "title": "Article Title",
        "content": "Article content...",
        "url": "https://example.com/article",
        "source": "@channelname",
        "published_date": "2023-01-01T12:00:00",
        "ai_summary": "AI generated summary",
        "category": "Technology"
      }
    ]
    ```
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
    
    Parameters:
    - **article_id** (path): The ID of the article to retrieve
    
    Returns:
    - **NewsArticle**: The requested article details
    
    Raises:
    - **401 Unauthorized**: When user is not authenticated
    - **404 Not Found**: When article with the specified ID doesn't exist
    
    Example response:
    ```json
    {
      "id": 1,
      "title": "Article Title",
      "content": "Article content...",
      "url": "https://example.com/article",
      "source": "@channelname",
      "published_date": "2023-01-01T12:00:00",
      "ai_summary": "AI generated summary",
      "category": "Technology"
    }
    ```
    """
    db_article = crud.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return db_article


@router.get("/sources/", response_model=List[str])
def get_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a list of all available news sources.
    
    Returns:
    - **List of strings**: All unique news sources in the database
    
    Raises:
    - **401 Unauthorized**: When user is not authenticated
    
    Example response:
    ```json
    [
      "@TechNews",
      "@WorldNews",
      "@SportsChannel"
    ]
    ```
    """
    # Query all distinct sources from the database
    sources = db.query(crud.NewsArticle.source).distinct().all()
    return [source[0] for source in sources if source[0]] 