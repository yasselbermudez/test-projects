from fastapi import APIRouter, Depends
from .schemas import User
from .service import get_current_user

router = APIRouter()

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user