from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_database
from .schemas import User,UpdateUser
from .service import get_current_user, get_current_user_id, update_user_info

router = APIRouter()

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/")
async def update_user(user_info: UpdateUser,user_id: str=Depends(get_current_user_id), db=Depends(get_database)):
    result = await update_user_info(user_id,user_info,db)
    return result