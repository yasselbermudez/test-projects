from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional

class EventResponse(BaseModel):
    id: str
    message: str
    success: bool

class Member(BaseModel):
    user_id: str
    user_name: str

class Group(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_name: str
    members: List[Member]
    created: datetime
    created_by: str
    creator_id: str

class UpdateGroup(BaseModel):
    group_name: str = None
    members: List[Member] = None

class UpdateMembers(BaseModel):
    user_id: str
    user_name: str
    remove: bool = False
    password: Optional[str] = None
    
class CreateGroup(BaseModel): 
    group_name: str
    current_user_id: str
    current_user_name: str
    password:str