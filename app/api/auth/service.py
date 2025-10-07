from typing import Optional
from app.core.security import get_password_hash
from fastapi import HTTPException
from .schemas import UserCreate, UserLogin, Token, User
from app.database.database import client as client_db, prepare_for_mongo, get_database

async def find_user_by_email(user_email:str,db) -> Optional[dict]:
    # Use the 'users' collection (ensure correct collection name)
    return await db.users.find_one({"email": user_email})
           
        
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
    
    # access_token = create_access_token(data={"sub": user_data_object.id})
    # return {"access_token": access_token, "token_type": "bearer", "user": user_data_object}
    
    return {"result":"creado"}