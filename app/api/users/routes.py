from fastapi import APIRouter, Depends, HTTPException

from app.database.database import get_database
from .schemas import User,UpdateUser
from .service import get_current_user

router = APIRouter()

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/{user_id}")
async def update_user_info(user_id: str, user_info: UpdateUser, db=Depends(get_database)):
    
    update_data = user_info.dict(exclude_none=True)
    
    try:
        result = await db.users.update_one(
            {"id": user_id},  # Buscar por el campo id
            {"$set": update_data}
        )
    except Exception as e:
        print(f"Error durante la actualizacion: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail="Update error")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"User not found")
    
    return {"message": "User info updated successfully"}