from typing import Optional
import jwt
from app.core.security import decode_access_token
from .schemas import UpdateUser, User
from app.database.database import parse_from_mongo, get_database
import logging

logger = logging.getLogger(__name__)

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
    except HTTPException:
        raise
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
async def update_user_info(user: User, user_info: UpdateUser, db)->User:
    try:
        update_data = user_info.dict(exclude_none=True)

        result = await db.users.update_one(
            {"id": user.id}, 
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Usuario {user.id} actualizado exitosamente")
            user_response = await db.users.find_one({"id": user.id})
        else:
            user_response = user
            logger.info(f"No se realizaron cambios para el usuario {user.id} ")
            
        return user_response
        
    except Exception as e:
        logger.error(f"Error interno al actualizar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar usuario"
        )