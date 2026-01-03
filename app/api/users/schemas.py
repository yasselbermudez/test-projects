from  datetime import datetime, timezone 
from typing import Optional
import uuid
from pydantic import BaseModel, Field

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = False
    group_id: Optional[str] = None
    
class UserInDb(User):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = False
    group_id: Optional[str] = None
    hashed_password: str

class UpdateUser(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    group_id: Optional[str] = None

