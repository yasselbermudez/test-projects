from typing import Optional
import jwt
from app.core.security import decode_access_token
from .schemas import UpdateUser, User, UserInDb
from app.database.database import parse_from_mongo, get_database
import logging
from fastapi import Depends, HTTPException,Request,status

logger = logging.getLogger(__name__)

async def get_user_by_id(user_id: str,db) -> UserInDb:
    try:
        user_data = await db.users.find_one({"id": user_id})
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserInDb(**parse_from_mongo(user_data))
    
    except Exception as e:
        logger.error(f"Error retrieving user by ID {user_id}: {str(e)}")
        raise   HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )

async def get_current_user(request: Request, db=Depends(get_database)) -> User:
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        # (opcional) verificar CSRF: comparar header 'x-csrf-token' con cookie 'csrf_token'
        payload = decode_access_token(token)
        # payload = {"user_id": 123, "exp": 1234567890, ...}
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user:UserInDb = await get_user_by_id(user_id,db)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # convertir a modelo público (sin hashed_password) antes de retornar
        return User(**user.dict())
    except HTTPException:
        raise
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
            user_db:UserInDb = await get_user_by_id(user.id,db)
            user_response = User(**user_db.dict())
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