from  datetime import datetime, timezone, timedelta 
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

class UserCreate(BaseModel):
    name:str
    email:str
    password: str
    role: str

class UserLogin(BaseModel):
    email:str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class RefreshToken(BaseModel):
    user_id: str
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    delete_at: datetime = Field(default_factory=datetime.utcnow)
    is_revoked: bool = False



