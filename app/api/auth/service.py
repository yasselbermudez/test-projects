from datetime import datetime, timedelta
import random
from typing import Optional
from app.core.config import settings
import jwt
from app.core.security import decode_refresh_token, get_password_hash, verify_password
from fastapi import HTTPException, Request,status
from .schemas import RefreshToken, UserCreate, UserLogin, User,UserInDb
from app.database.database import prepare_for_mongo, parse_from_mongo
import logging

logger = logging.getLogger(__name__)

async def validate_user_by_email(user_email:str,db) -> bool:
    try:
        result = await db.emails.find_one({"email": user_email})
        if result:
            return True
        return False
    except:
        return False
    
async def find_user_by_email(user_email:str,db) -> Optional[UserInDb]:
    return await db.users.find_one({"email": user_email})

async def get_user_by_id(user_id: str,db) -> Optional[UserInDb]:
    return await db.users.find_one({"id": user_id})           
        
async def create_user(user_data:UserCreate,db) -> User:
    
    existing_user = await find_user_by_email(user_data.email,db)
    
    if existing_user :
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="User email already registered")
    
    valid_user = await validate_user_by_email(user_data.email,db)
    if not valid_user : 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email")

    hashed_password=get_password_hash(user_data.password)
    
    user_data_dict = user_data.dict()
    
    del user_data_dict["password"]

    user_data_object = User(**user_data_dict)

    user_data_doc = prepare_for_mongo(user_data_object.dict())
    
    user_data_doc["hashed_password"] = hashed_password

    await db.users.insert_one(user_data_doc)
    
    return  user_data_object


async def authenticate_user(login_data:UserLogin,db) -> User:
    try:
        existing_user = await find_user_by_email(login_data.email,db)
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        hashed_password = existing_user.get('hashed_password')
        is_verify = verify_password(login_data.password, hashed_password)

        if not is_verify:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        user_obj = User(**parse_from_mongo(existing_user))

        return  user_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication error")

async def save_refresh_token_to_db(
    user_id: str, 
    token: str, 
    db
) -> str:
    try:
        
        expires_at = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        variation = timedelta(hours=random.randint(0, 12))
        delete_at = datetime.utcnow() + timedelta(days=30) + variation
        
        refresh_token_obj = RefreshToken(
            user_id=user_id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            delete_at=delete_at,
            is_revoked=False
        )
        
        result = await db.refresh_tokens.insert_one(refresh_token_obj.dict())
        if result.inserted_id is None:
            raise Exception("Failed to insert refresh token")
        
        await cleanup_old_refresh_tokens(user_id, db)

        return result.inserted_id
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving refresh token: {str(e)}")


async def validate_and_revoke_refresh_token(user_id: str, token: str, db) -> bool:

    token_doc = await db.refresh_tokens.find_one({
        "user_id": user_id,
        "token": token,
        "is_revoked": False
    })
    
    if not token_doc:
        return False
    
    # verify expire at
    expires_at = token_doc.get("expires_at")
    if expires_at and expires_at < datetime.utcnow():
        await revoke_refresh_token_by_id(token_doc["_id"], db)
        return False
    
    await revoke_refresh_token_by_id(token_doc["_id"], db)
    return True

async def cleanup_old_refresh_tokens(user_id: str, db, max_tokens: int = 2) -> None:
    try:
        # Obtain the tokens sorted by creation
        tokens = await db.refresh_tokens.find(
            {"user_id": user_id, "is_revoked": False}
        ).sort("created_at", -1).to_list(length=None)
        
        # Revoke the oldest ones
        if len(tokens) > max_tokens:
            tokens_to_revoke = tokens[max_tokens:]
            
            for token in tokens_to_revoke:
                await revoke_refresh_token_by_id(token["_id"], db)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error cleaning up old refresh tokens")

async def revoke_all_user_refresh_tokens(user_id: str, db) -> None:
    try:
        await db.refresh_tokens.update_many(
            {"user_id": user_id, "is_revoked": False},
            {"$set": {"is_revoked": True}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error revoking all refresh token")
    
async def revoke_refresh_token(token: str, db) -> None:
    try:
        await db.refresh_tokens.update_one(
            {"token": token},
            {"$set": {"is_revoked": True}}
        )
    except Exception as e:
        logger.error(f"Error revoking refresh token: {str(e)}")
        raise HTTPException(status_code=500, detail="Error revoking refresh token")
    
async def revoke_refresh_token_by_id(id: str, db) -> None:
    try:
        await db.refresh_tokens.update_one(
            {"_id": id},
            {"$set": {"is_revoked": True}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error revoking refresh token")

async def refresh_access_token(request:Request, db) -> User:

    try:
        token = request.cookies.get("refresh_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
        
        payload = decode_refresh_token(token)
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        if not await validate_and_revoke_refresh_token(user_id,token,db):
            raise HTTPException(status_code=400, detail="Invalid refresh token")

        # get user data
        existing_user = await get_user_by_id(user_id,db)
        user_obj = User(**parse_from_mongo(existing_user))

        return user_obj
        
    except HTTPException:
        raise
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refres token")