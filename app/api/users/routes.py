from fastapi import APIRouter, Depends
from app.database.database import get_database
from .schemas import User,UpdateUser
from .service import get_current_user, update_user_info

router = APIRouter()

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("",response_model=User)
async def update_user(user_info: UpdateUser,user: User =Depends(get_current_user), db=Depends(get_database)):
    return await update_user_info(user,user_info,db)
    