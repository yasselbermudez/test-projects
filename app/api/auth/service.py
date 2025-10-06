from typing import Optional
from app.core.security import get_password_hash
from fastapi import HTTPException
from .schemas import UserCreate, UserLogin, Token, User, UserInDb

fake_users_db:User = [
    {
        "id":"1",
        "name":"yassel",
        "email":"yassel@gmail.com",
        "hashed_password":"12345678#hashed",
        "is_active":True
    }
]

def find_user(user_email:str) -> User:
    for fake_user in fake_users_db:
        if fake_user["email"] == user_email:
            return fake_user
        
def create(user_in:UserCreate):
    user = UserInDb(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        id=len(fake_users_db)+1,
        is_active=True
    )
    print(user)
    fake_users_db.append(user)

def create_user(user_data:UserCreate):
    user = find_user(user_data.email)
    if user :
        raise HTTPException(status_code=400,detail="User email already registered")
    return create(user_data)
