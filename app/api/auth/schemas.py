from  datetime import datetime, timezone 
import uuid
from pydantic import BaseModel, Field

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserCreate(BaseModel):
    name:str
    email:str
    password: str

class UserLogin(BaseModel):
    email:str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User



