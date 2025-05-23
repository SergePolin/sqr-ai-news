from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ArticleBase(BaseModel):
    title: str
    content: str
    url: str
    source: str
    published_date: datetime


class NewsArticle(ArticleBase):
    id: int
    sentiment_score: Optional[float] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ArticleCreate(ArticleBase):
    sentiment_score: Optional[float] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    ai_summary: Optional[str] = None


class Bookmark(BaseModel):
    id: int
    user_id: str
    article_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Alias for backward compatibility with tests and other modules
NewsArticleBase = ArticleBase
