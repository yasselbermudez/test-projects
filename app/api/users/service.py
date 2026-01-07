import jwt
from app.core.security import decode_access_token
from .schemas import UpdateUser, User, UserInDb
from app.database.database import parse_from_mongo, get_database
import logging
from fastapi import Depends, HTTPException,Request,status

logger = logging.getLogger(__name__)

async def get_user_by_id(user_id: str,db) -> UserInDb:
    try:
        logger.info(f"Retrieving user by id: {user_id}")
        user_data = await db.users.find_one({"id": user_id})
        if not user_data:
            logger.error(f"User with id {user_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with id {user_id} not found")
        return UserInDb(**parse_from_mongo(user_data))
    
    except Exception as e:
        logger.error(f"Error retrieving user by id: {str(e)}")
        raise   HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user by id: {str(e)}"
        )

async def get_current_user(request: Request, db=Depends(get_database)) -> User:
    try:
        logger.info("Retrieving current user from token")
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        # (opcional) verificar CSRF: comparar header 'x-csrf-token' con cookie 'csrf_token'
        
        payload = decode_access_token(token)
        
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.error("Invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")

        user:UserInDb = await get_user_by_id(user_id,db)
        if user is None:
            logger.error("User not found")
            raise HTTPException(status_code=401, detail="User not found")
        
        # Public model
        return User(**user.dict())
    except HTTPException:
        raise
    except jwt.PyJWTError as e:
        logger.error(f"Invalid token error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token error: {str(e)}")

async def get_current_user_id(request: Request, db=Depends(get_database)) -> str:
    try:
        logger.info("Retrieving current user ID from token")
        token = request.cookies.get("access_token")
        if not token:
            logger.error("No access token found in cookies")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access token found in cookies")
        payload = decode_access_token(token)
        
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.error("User ID not found in token payload")
            raise HTTPException(status_code=401, detail="User ID not found in token payload")
        
        return user_id
    except HTTPException:
        raise
    except jwt.PyJWTErrora as e:
        logger.error(f"Invalid token error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token error: {str(e)}")
    
async def update_user_info(user: User, user_info: UpdateUser, db)->User:
    try:
        logger.info(f"Updating user {user.id}")
        update_data = user_info.dict(exclude_none=True)

        result = await db.users.update_one(
            {"id": user.id}, 
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"User {user.id} updated successfully")
            user_db:UserInDb = await get_user_by_id(user.id,db)
            user_response = User(**user_db.dict())
        else:
            user_response = user
            logger.info(f"No changes were made to the user {user.id} ")
            
        return user_response
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )