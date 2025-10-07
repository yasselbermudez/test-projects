from fastapi import APIRouter, Depends, status
from .schemas import UserCreate, UserLogin, Token, User
from . import service
from app.database.database import get_database

router = APIRouter()

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate,db=Depends(get_database)):
    result =  await service.create_user(user_data,db)
    return result

"""
@router.post("/login", response_model=Token)
async def login_user(login_data: UserLogin):
    result = await service.authenticate_user(login_data.email, login_data.password)
    return result


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(service.get_current_user)):
    return current_user
"""