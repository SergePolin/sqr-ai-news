from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.db.database import get_db
from app.db import crud

router = APIRouter()

@router.post("/feed", response_model=ChannelResponse)
def create_feed(channel: ChannelCreate, db: Session = Depends(get_db)):
    # Calling the channel creation function from the CRUD module
    created_channel = crud.create_user_channel(db, user_id=channel.user_id, channel_alias=channel.channel_alias)
    if not created_channel:
        raise HTTPException(status_code=400, detail="Channel creation failed")
    return created_channel