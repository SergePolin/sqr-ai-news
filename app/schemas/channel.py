from datetime import datetime
# from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ChannelBase(BaseModel):
    Channel_alias: str


class ChannelCreate(ChannelBase):
    pass


class ChannelResponse(BaseModel):
    id: UUID
    user_id: str
    channel_alias: str
    created_at: datetime

    class Config:
        orm_mode = True
