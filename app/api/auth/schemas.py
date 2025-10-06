import uuid
from pydantic import BaseModel, Field

class UserInDb(BaseModel):
    id: int
    email: str
    name: str
    hashed_password:str
    is_active: bool = True

class User(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool = True

class UserCreate(BaseModel):
    email:str
    password: str
    name:str

class UserLogin(BaseModel):
    email:str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User



