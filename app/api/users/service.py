from typing import Optional
import jwt
from app.core.security import decode_access_token
from .schemas import UpdateUser, User
from app.database.database import parse_from_mongo, get_database

async def get_user_by_id(user_id: str,db) -> Optional[dict]:
    return await db.users.find_one({"id": user_id})

"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login") # Solo documentación, no redirige
CON oauth2_scheme
Cliente envía request:
httpGET /api/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

"""
from fastapi import Depends, HTTPException,Request,status
"""Dependencia para rutas que requieren autenticación vía token en cookie"""

async def get_current_user(request: Request, db=Depends(get_database)) -> User:
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        # 2) (opcional) verificar CSRF: comparar header 'x-csrf-token' con cookie 'csrf_token'
        # 3) decodificar token y recuperar user
        payload = decode_access_token(token)
        # payload = {"user_id": 123, "exp": 1234567890, ...}
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await get_user_by_id(user_id,db)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # convertir a modelo público (sin hashed_password) antes de retornar
        return User(**parse_from_mongo(user))
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_id(request: Request, db=Depends(get_database)) -> str:
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        payload = decode_access_token(token)
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
async def update_user_info(user_id: str, user_info: UpdateUser, db) -> dict:
    update_data = user_info.dict(exclude_none=True)
    
    try:
        result = await db.users.update_one(
            {"id": user_id}, 
            {"$set": update_data}
        )
    except Exception as e:
        print(f"Error durante la actualizacion: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail="Update error")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"User not found")
    
    return {"message": "User info updated successfully"}