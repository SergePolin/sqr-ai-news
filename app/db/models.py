from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func

from app.db.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text)
    url = Column(String(255), unique=True, index=True)
    source = Column(String(100))
    published_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # AI-related fields
    sentiment_score = Column(Float, nullable=True)
    category = Column(String(50), nullable=True)
    keywords = Column(String(255), nullable=True) 