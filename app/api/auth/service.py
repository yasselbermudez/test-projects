from typing import Optional
import jwt
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import get_password_hash, verify_password, create_access_token,decode_access_token
from fastapi import HTTPException
from .schemas import UserCreate, UserLogin, User,UserInDb
from app.database.database import prepare_for_mongo, parse_from_mongo

async def find_user_by_email(user_email:str,db) -> Optional[UserInDb]:
    # Use the 'users' collection (ensure correct collection name)
    return await db.users.find_one({"email": user_email})

async def get_user_by_id(user_id: str,db) -> Optional[dict]:
    return await db.users.find_one({"id": user_id})           
        
async def create_user(user_data:UserCreate,db) -> dict:
    
    existing_user = await find_user_by_email(user_data.email,db)
    
    if existing_user :
        raise HTTPException(status_code=400,detail="User email already registered")
    
    hashed_password=get_password_hash(user_data.password)
    
    user_data_dict = user_data.dict()
    
    del user_data_dict["password"]

    user_data_object = User(**user_data_dict)

    user_data_doc = prepare_for_mongo(user_data_object.dict())
    
    user_data_doc["hashed_password"] = hashed_password

    await db.users.insert_one(user_data_doc)
    
    access_token = create_access_token(data={"sub": user_data_object.id})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_data_object}

async def authenticate_user(login_data:UserLogin,db) -> dict:
    
    existing_user = await find_user_by_email(login_data.email,db)
    hashed_password = existing_user.get('hashed_password')
    is_verify = verify_password(login_data.password, hashed_password)

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not existing")
    if not is_verify:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_obj = UserInDb(**parse_from_mongo(existing_user))

    access_token = create_access_token(data={"sub": user_obj.id})

    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}

