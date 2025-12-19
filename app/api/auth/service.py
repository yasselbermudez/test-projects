from typing import Optional
from app.core.security import get_password_hash, verify_password, create_access_token
from fastapi import HTTPException,status
from .schemas import UserCreate, UserLogin, User,UserInDb
from app.database.database import prepare_for_mongo, parse_from_mongo

valid_emails = ["javiersarduy0123@gmail.com","lazaroarielmachado@gmail.com","luisangelalfonso43@gmail.com","rodriguezrodriguezm163@gmail.com","yasselbermudez8@gmail.com"]
# solucion temporal solo para desarrollo
async def validate_user_by_email(user_email:str,db) -> bool:
    for email in valid_emails:
        if email==user_email:
            return True
    return False

async def find_user_by_email(user_email:str,db) -> Optional[UserInDb]:
    # Use the 'users' collection (ensure correct collection name)
    return await db.users.find_one({"email": user_email})

async def get_user_by_id(user_id: str,db) -> Optional[UserInDb]:
    return await db.users.find_one({"id": user_id})           
        
async def create_user(user_data:UserCreate,db) -> dict:
    
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
    
    access_token = create_access_token(data={"sub": user_data_object.id})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_data_object}

async def authenticate_user(login_data:UserLogin,db) -> dict:
    
    existing_user = await find_user_by_email(login_data.email,db)
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    hashed_password = existing_user.get('hashed_password')
    is_verify = verify_password(login_data.password, hashed_password)

    if not is_verify:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user_obj = UserInDb(**parse_from_mongo(existing_user))

    access_token = create_access_token(data={"sub": user_obj.id})

    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}

