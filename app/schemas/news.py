from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class NewsArticleBase(BaseModel):
    title: str
    content: str
    url: str
    source: str
    published_date: Optional[datetime] = None


class NewsArticle(NewsArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    sentiment_score: Optional[float] = None
    category: Optional[str] = None
    keywords: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True 