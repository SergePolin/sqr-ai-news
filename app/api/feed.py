from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    BackgroundTasks,
    status
)
from sqlalchemy.orm import Session
# from typing import List
# import uuid
from datetime import datetime, timedelta
import feedparser
import requests
from bs4 import BeautifulSoup
import time
import logging

from app.db.database import get_db
from app.db.crud import (
    add_user_channel, get_user_channels,
    create_or_update_article, get_articles,
    get_article_by_url, add_bookmark,
    remove_bookmark, get_user_bookmarks
)
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.core.dependencies import get_current_active_user
from app.db.models import User, NewsArticle as NewsArticleModel
from app.core.ai import generate_article_summary, generate_article_category
from app.schemas.news import Bookmark, NewsArticle

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feed", tags=["feed"])


def process_channel_articles(channel_alias: str, db: Session, max_articles: int = 90, retry_count: int = 3):
    """
    Background task to fetch and process articles from a channel.
    
    Args:
        channel_alias: The Telegram channel alias to fetch articles from
        db: Database session
        max_articles: Maximum number of articles to process in one run
        retry_count: Number of times to retry on failure
    """
    # Form the request URL for RSShub
    rss_url = (
        f"https://rsshub.app/telegram/channel/"
        f"{channel_alias.lstrip('@')}"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }

    logger.info(f"Starting to process articles for channel: {channel_alias}")
    
    for attempt in range(retry_count):
        try:
            # RSS Feed parsing
            logger.info(f"Fetching RSS feed from {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=15)
            
            # Handle rate limiting specifically
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', (attempt + 1) * 5))
                logger.warning(f"Rate limited (429) - will retry after {retry_after} seconds")
                time.sleep(retry_after)
                continue
                
            if response.status_code != 200:
                logger.error(f"Failed to fetch RSS feed: HTTP {response.status_code}")
                time.sleep(3 + (attempt * 2))  # Wait before retry with increasing backoff
                continue
                
            rss_feed = feedparser.parse(response.content)
            
            if not rss_feed.entries:
                logger.warning(f"No entries found in RSS feed for {channel_alias}")
                return
                
            logger.info(f"Found {len(rss_feed.entries)} entries in feed for {channel_alias}")
            
            # Process only up to max_articles
            processed = 0
            new_articles = 0
            
            for entry in rss_feed.entries[:max_articles]:
                # Check for duplicate by URL
                article_url = entry.get("link", "")
                if not article_url:
                    logger.warning("Skipping entry without URL")
                    continue
                    
                if get_article_by_url(db, article_url):
                    logger.debug(f"Skipping duplicate article: {article_url}")
                    continue
                
                # Extract content
                html_content = entry.get("description", "")
                soup = BeautifulSoup(html_content, "html.parser")
                plain_text = soup.get_text()
                
                if len(plain_text.strip()) < 50:
                    logger.warning(f"Article content too short: {article_url}")
                    continue
                
                # Generate AI summary and category
                logger.info(f"Generating AI summary and category for: {entry.get('title', 'Untitled')}")
                ai_summary = generate_article_summary(plain_text)
                category = generate_article_category(
                    plain_text, entry.get("title", ""))

                # Prepare article data
                try:
                    published_date = datetime.strptime(
                        entry.get("published", datetime.now().isoformat()),
                        "%a, %d %b %Y %H:%M:%S %Z"
                    ) if "published" in entry else datetime.now()
                except ValueError as e:
                    logger.error(f"Date parsing error: {str(e)}")
                    published_date = datetime.now()
                
                article_data = {
                    "title": entry.get("title", ""),
                    "content": plain_text,
                    "url": article_url,
                    "source": channel_alias,
                    "published_date": published_date,
                    "ai_summary": ai_summary,
                    "category": category
                }

                # Create or update article in database
                created = create_or_update_article(db, article_data)
                processed += 1
                if created:
                    new_articles += 1
                    logger.info(f"Added new article: {article_data['title']}")
                
                # Add a delay to avoid overwhelming the AI service and rate limits
                time.sleep(1.0)
                
            logger.info(f"Channel {channel_alias} processed {processed} articles, {new_articles} new")
            return  # Success, exit function
            
        except requests.RequestException as e:
            logger.error(f"Request error (attempt {attempt+1}/{retry_count}): {str(e)}")
            if attempt < retry_count - 1:
                sleep_time = 5 * (attempt + 1)  # Longer exponential backoff
                logger.info(f"Retrying in {sleep_time} seconds")
                time.sleep(sleep_time)
        except Exception as e:
            logger.error(f"Error processing channel {channel_alias}: {str(e)}")
            return  # On general error, exit function
    
    logger.error(f"Failed to process channel {channel_alias} after {retry_count} attempts")


@router.post("/", response_model=ChannelResponse)
def create_channel(
    channel: ChannelCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a new channel to user's feed and process its articles.

    Parameters:
    - **channel**: Channel information containing the channel alias

    Returns:
    - **Channel information**: Created channel details including ID

    Raises:
    - **401 Unauthorized**: When the user is not authenticated

    Example request:
    ```json
    {
      "Channel_alias": "@channelname"
    }
    ```

    Notes:
    - Adds the channel to the user's subscriptions
    - Starts a background task to fetch and store articles
    - Generates AI summaries for articles
    """
    # Add channel to user's subscriptions
    channel_record = add_user_channel(db=db, user_id=str(
        current_user.id), channel_alias=channel.Channel_alias)

    # Start background task to process articles
    background_tasks.add_task(process_channel_articles,
                              channel.Channel_alias, db)

    return channel_record


@router.get("/")
def get_channels_with_articles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    generate_summaries: bool = Query(
        False, description="Generate AI summaries for articles"),
    generate_categories: bool = Query(
        False, description="Generate AI categories for articles")
):
    """
    Get all channels and their articles for the authenticated user.

    Parameters:
    - **generate_summaries** (query, optional):
        Flag to generate AI summaries for articles
    - **generate_categories** (query, optional):
        Flag to generate AI categories for articles

    Returns:
    - **List of channels with articles**:
        Each channel includes its articles with metadata, sorted by date (newest first)

    Raises:
    - **401 Unauthorized**: When the user is not authenticated

    Example response:
    ```json
    [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "channel_alias": "@channelname",
        "articles": [
          {
            "id": 1,
            "title": "Article Title",
            "description": "Article content...",
            "link": "https://example.com/article",
            "published_date": "2023-01-01T12:00:00",
            "ai_summary": "AI generated summary",
            "category": "Technology"
          }
        ]
      }
    ]
    ```
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
        # Articles are already sorted by published_date desc (newest first) in get_articles
        articles_db = get_articles(db, source=channel.channel_alias)
        articles = []
        for article in articles_db:
            articles.append({
                "id": article.id,
                "title": article.title,
                "description": article.content,
                "link": article.url,
                "published_date": (
                    article.published_date.isoformat()
                    if article.published_date
                    else None
                ),
                "ai_summary": article.ai_summary,
                "category": article.category
            })
            
        # Double-check articles are properly sorted by published_date (newest first)
        articles.sort(
            key=lambda x: x["published_date"] if x["published_date"] else "0", 
            reverse=True
        )
            
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
    current_user: User = Depends(get_current_active_user),
    max_articles_per_channel: int = Query(90, description="Maximum articles to fetch per channel")
):
    """
    Trigger an update to fetch new articles for all user's channels.

    Parameters:
    - **max_articles_per_channel** (query, optional): 
        Maximum number of articles to fetch per channel. Default: 90

    Returns:
    - **Message**: Confirmation that update has been started

    Raises:
    - **401 Unauthorized**: When the user is not authenticated
    - **404 Not Found**: When no channels are found for the user

    Example response:
    ```json
    {
      "message": "Update started for all channels."
    }
    ```

    Notes:
    - This is an asynchronous operation using background tasks
    - Articles are fetched from Telegram channels via RSS
    - Rate limiting can occur when too many requests are made
    """
    channels = get_user_channels(db=db, user_id=str(current_user.id))
    if not channels:
        raise HTTPException(
            status_code=404, detail="No channels found for user.")
    
    channel_count = len(channels)
    logger.info(f"Starting update for {channel_count} channels for user {current_user.username}")
    
    # Add small delays between channel processing tasks to avoid overwhelming the RSS service
    for idx, channel in enumerate(channels):
        # Add a gradually increasing delay for each channel to avoid rate limiting
        background_tasks.add_task(
            process_channel_articles, 
            channel.channel_alias, 
            db, 
            max_articles_per_channel
        )
        # Add a small delay between scheduling tasks
        if idx < len(channels) - 1:
            time.sleep(0.5)
    
    return {
        "message": f"Update started for {channel_count} channels. New articles will be available shortly."
    }


@router.post(
    "/bookmarks/{article_id}", response_model=Bookmark,
    status_code=status.HTTP_201_CREATED
)
def add_article_bookmark(
    article_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add an article to user's bookmarks.

    Parameters:
    - **article_id** (path): ID of the article to bookmark

    Returns:
    - **Bookmark**: Created bookmark information

    Raises:
    - **401 Unauthorized**: When user is not authenticated
    - **404 Not Found**: When article is not found

    Example response:
    ```json
    {
      "id": 1,
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "article_id": 42,
      "created_at": "2023-01-01T12:00:00"
    }
    ```
    """
    return add_bookmark(db, str(current_user.id), article_id)


@router.delete(
    "/bookmarks/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_article_bookmark(
    article_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove an article from user's bookmarks.

    Parameters:
    - **article_id** (path): ID of the article to remove from bookmarks

    Returns:
    - No content response (204)

    Raises:
    - **401 Unauthorized**: When user is not authenticated
    - **404 Not Found**: When bookmark is not found
    """
    removed = remove_bookmark(db, str(current_user.id), article_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Bookmark not found.")
    return


@router.get("/bookmarks", response_model=list[NewsArticle])
def list_user_bookmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all articles bookmarked by the current user.

    Returns:
    - **List of NewsArticle**: All bookmarked articles with their details

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
    bookmarks = get_user_bookmarks(db, str(current_user.id))
    article_ids = [b.article_id for b in bookmarks]
    if not article_ids:
        return []
    articles = db.query(NewsArticleModel).filter(
        NewsArticleModel.id.in_(article_ids)).all()
    return articles
