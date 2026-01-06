from typing import Optional
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from app.core.config import settings
from datetime import datetime, timedelta
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_SECRET_KEY=settings.ACCESS_TOKEN_SECRET_KEY
REFRESH_TOKEN_SECRET_KEY=settings.REFRESH_TOKEN_SECRET_KEY
ALGORITHM=settings.ALGORITHM

def verify_password(plain_password: str, hashed_password: str) -> bool:
    "Verify plaintext password against hash"
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    "Get password hash"
    return pwd_context.hash(password)

def create_access_token(data: dict,expires_delta:Optional[timedelta] = None)-> str :
    """Create access JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    token = jwt.encode(to_encode, ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return token

def create_refresh_token(data: dict,expires_delta:Optional[timedelta] = None)-> str :
    """Create refresh JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    token = jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_access_token(token: str) -> Optional[dict]:
    """Decode access JWT token"""
    try:
        payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except InvalidTokenError:
        return None
    
def decode_refresh_token(token: str):
    """Decode refresh JWT token"""
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")