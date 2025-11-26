from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Event(BaseModel):
    user_id: str
    mission_id: str
    name: str
    tipo: str
    result: str
    status:str
    created: datetime = Field(default_factory=datetime.now)
    logro_name: Optional[str] = None

class EventResponse(BaseModel):
    id: str
    message: str
    success: bool
