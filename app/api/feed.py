from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
import feedparser
import requests
from bs4 import BeautifulSoup

from app.db.database import get_db
from app.db.crud import add_user_channel, get_user_channels, create_or_update_article
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.core.dependencies import get_current_active_user
from app.db.models import User
from app.core.ai import generate_article_summary, generate_article_category

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
                "url": entry.get("link", ""),
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
    
    Parameters:
    - generate_summaries: Set to true to generate AI summaries for articles
    - generate_categories: Set to true to generate AI categories for articles
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

    # For each channel, request and parse the RSS feed
    for channel in unique_channels.values():
        # Form the request URL for RSShub
        rss_url = f"https://rsshub.app/telegram/channel/{channel.channel_alias.lstrip('@')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

        try:
            # RSS Feed parsing
            response = requests.get(rss_url, headers=headers)
            rss_feed = feedparser.parse(response.content)
            
            articles = []

            # Extract articles with required fields: title, description and link
            for entry in rss_feed.entries:
                html_content = entry.get("description", "")
                soup = BeautifulSoup(html_content, "html.parser")
                plain_text = soup.get_text()
                
                # Generate AI summary and category if requested
                ai_summary = None
                category = None
                
                if generate_summaries:
                    ai_summary = generate_article_summary(plain_text)
                    
                if generate_categories:
                    category = generate_article_category(plain_text, entry.get("title", ""))

                articles.append({
                    "title": entry.get("title", ""),
                    "description": plain_text,
                    "link": entry.get("link", ""),
                    "published_date": entry.get("published", datetime.now().isoformat()),
                    "ai_summary": ai_summary,
                    "category": category
                })

            feed_results.append({
                "id": str(channel.id),
                "channel_alias": channel.channel_alias,
                "articles": articles
            })
        except Exception as e:
            # Log exception and continue with next channel
            print(f"Error fetching channel {channel.channel_alias}: {str(e)}")
            feed_results.append({
                "id": str(channel.id),
                "channel_alias": channel.channel_alias,
                "articles": [{"title": "Error fetching articles", 
                              "description": f"Could not fetch articles: {str(e)}", 
                              "link": "#",
                              "published_date": datetime.now().isoformat(),
                              "ai_summary": None,
                              "category": None}]
            })
    
    return feed_results

# Legacy endpoint - can be removed after frontend is updated
@router.get("/feed")
def get_feed(userID: str, db: Session = Depends(get_db)):
    # We get all the user's channels from the DB
    channels = get_user_channels(db, userID)

    if not channels:
        raise HTTPException(status_code=404, detail="User channels not found")
    
    feed_results = []

    unique_channels = {}
    for channel in channels:
        if channel.channel_alias not in unique_channels:
            unique_channels[channel.channel_alias] = channel

    # For each channel, we request and parse the RSS feed.
    for channel in unique_channels.values():
        # Forming the request URL
        rss_url = f"https://rsshub.app/telegram/channel/{channel.channel_alias.lstrip('@')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

        # RSS Feed parsing
        response = requests.get(rss_url, headers=headers)
        rss_feed = feedparser.parse(response.content)
        
        articles = []

        # We extract articles with the required fields: title, description and link
        for entry in rss_feed.entries:
            html_content = entry.get("description", "")
            soup = BeautifulSoup(html_content, "html.parser")
            plain_text = soup.get_text()

            articles.append({
                "title": entry.get("title", ""),
                "description": plain_text,
                "link": entry.get("link", "")
            })

        feed_results.append({
            "channel_alias": channel.channel_alias,
            "articles": articles
        })
    return feed_results