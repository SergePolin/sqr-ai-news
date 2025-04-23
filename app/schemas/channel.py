from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ChannelCreate(BaseModel):
    user_id: str = Field(..., alias="UserID")
    channel_alias: str = Field(..., alias="Channel_alias")

    # Allows to accept data by name from alias
    class Config:
        allow_population_by_field_name = True

class ChannelResponse(BaseModel):
    id: UUID
    user_id: str
    channel_alias: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True