from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.db.database import get_db
from app.db import crud
from typing import List, Dict
import feedparser
import requests
from bs4 import BeautifulSoup

router = APIRouter()

@router.post("/feed", response_model=ChannelResponse)
def create_feed(channel: ChannelCreate, db: Session = Depends(get_db)):
    # Calling the channel creation function from the CRUD module
    created_channel = crud.create_user_channel(db, user_id=channel.user_id, channel_alias=channel.channel_alias)
    if not created_channel:
        raise HTTPException(status_code=400, detail="Channel creation failed")
    return created_channel

@router.get("/feed")
def get_feed(userID: str, db: Session = Depends(get_db)):
    # We get all the user's channels from the DB
    channels = crud.get_user_channels(db, userID)

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