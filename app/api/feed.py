from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
import feedparser
import requests
from bs4 import BeautifulSoup

from app.db.database import get_db
from app.db.crud import add_user_channel, get_user_channels, create_or_update_article, get_articles, get_article_by_url, add_bookmark, remove_bookmark, get_user_bookmarks, is_bookmarked
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.core.dependencies import get_current_active_user
from app.db.models import User, NewsArticle as NewsArticleModel
from app.core.ai import generate_article_summary, generate_article_category
from app.schemas.news import Bookmark, NewsArticle

router = APIRouter(prefix="/feed", tags=["feed"])


def process_channel_articles(channel_alias: str, db: Session):
    """
    Background task to fetch and process articles from a channel.
    """
    # Form the request URL for RSShub
    rss_url = f"https://rsshub.app/telegram/channel/{channel_alias.lstrip('@')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        # RSS Feed parsing
        response = requests.get(rss_url, headers=headers)
        rss_feed = feedparser.parse(response.content)
        
        for entry in rss_feed.entries:
            # Check for duplicate by URL
            article_url = entry.get("link", "")
            if get_article_by_url(db, article_url):
                continue  # Skip duplicate
            # Extract content
            html_content = entry.get("description", "")
            soup = BeautifulSoup(html_content, "html.parser")
            plain_text = soup.get_text()
            
            # Generate AI summary and category
            ai_summary = generate_article_summary(plain_text)
            category = generate_article_category(plain_text, entry.get("title", ""))
            
            # Prepare article data
            article_data = {
                "title": entry.get("title", ""),
                "content": plain_text,
                "url": article_url,
                "source": channel_alias,
                "published_date": datetime.strptime(entry.get("published", datetime.now().isoformat()), 
                                                   "%a, %d %b %Y %H:%M:%S %Z") 
                                 if "published" in entry else datetime.now(),
                "ai_summary": ai_summary,
                "category": category
            }
            
            # Create or update article in database
            create_or_update_article(db, article_data)
            
    except Exception as e:
        print(f"Error processing channel {channel_alias}: {str(e)}")


@router.post("/", response_model=ChannelResponse)
def create_channel(
    channel: ChannelCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a new channel to user's feed and process its articles.
    
    - Adds the channel to the user's subscriptions
    - Starts a background task to fetch and store articles
    - Generates AI summaries for articles
    """
    # Add channel to user's subscriptions
    channel_record = add_user_channel(db=db, user_id=str(current_user.id), channel_alias=channel.Channel_alias)
    
    # Start background task to process articles
    background_tasks.add_task(process_channel_articles, channel.Channel_alias, db)
    
    return channel_record


@router.get("/")
def get_channels_with_articles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    generate_summaries: bool = Query(False, description="Generate AI summaries for articles"),
    generate_categories: bool = Query(False, description="Generate AI categories for articles")
):
    """
    Get channels with articles for the authenticated user.
    Now returns articles from the database, not from RSS.
    """
    # Get all the user's channels from the DB
    channels = get_user_channels(db=db, user_id=str(current_user.id))
    
    if not channels:
        return []
    
    feed_results = []
    
    # Process unique channels only
    unique_channels = {}
    for channel in channels:
        if channel.channel_alias not in unique_channels:
            unique_channels[channel.channel_alias] = channel

    for channel in unique_channels.values():
        # Fetch articles for this channel from the DB (source == channel_alias)
        articles_db = get_articles(db, source=channel.channel_alias)
        articles = []
        for article in articles_db:
            articles.append({
                "id": article.id,
                "title": article.title,
                "description": article.content,
                "link": article.url,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "ai_summary": article.ai_summary,
                "category": article.category
            })
        feed_results.append({
            "id": str(channel.id),
            "channel_alias": channel.channel_alias,
            "articles": articles
        })
    return feed_results


@router.post("/update")
def update_all_channels(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger fetching and updating articles for all of the current user's channels from Telegram.
    """
    channels = get_user_channels(db=db, user_id=str(current_user.id))
    if not channels:
        raise HTTPException(status_code=404, detail="No channels found for user.")
    for channel in channels:
        background_tasks.add_task(process_channel_articles, channel.channel_alias, db)
    return {"message": "Update started for all channels."}


@router.post("/bookmarks/{article_id}", response_model=Bookmark, status_code=status.HTTP_201_CREATED)
def add_article_bookmark(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Add a bookmark for the current user and article."""
    return add_bookmark(db, str(current_user.id), article_id)

@router.delete("/bookmarks/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article_bookmark(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Remove a bookmark for the current user and article."""
    removed = remove_bookmark(db, str(current_user.id), article_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Bookmark not found.")
    return

@router.get("/bookmarks", response_model=list[NewsArticle])
def list_user_bookmarks(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """List all bookmarked articles for the current user."""
    bookmarks = get_user_bookmarks(db, str(current_user.id))
    article_ids = [b.article_id for b in bookmarks]
    if not article_ids:
        return []
    articles = db.query(NewsArticleModel).filter(NewsArticleModel.id.in_(article_ids)).all()
    return articles