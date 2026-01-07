from app.api.errors import ERROR_CODES
from app.api.users.schemas import UpdateUser, User
from .schemas import EventResponse, Profile, ProfileInit, ProfileUpdate
from app.database.database import parse_from_mongo, prepare_for_mongo
from fastapi import HTTPException,status
import logging
from app.api.users.service import update_user_info
from app.api.assignments.service import create_assignments

logger = logging.getLogger(__name__)

async def initialize_profile_data(
    user: User,
    profile_init_data: ProfileInit, 
    db
):
    
    try:
        logger.info(f"Initializing profile for user {user.id}")
        existing_profile = await db.profiles.find_one({"user_id": user.id})
        
        if existing_profile:
            logger.error("Profile already exists")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Profile already exists")

        # Init profile data
        profile_dict = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "edad": profile_init_data.edad,
            "estatura": profile_init_data.estatura,
            "peso_corporal": profile_init_data.peso_corporal,
            "pesos": profile_init_data.pesos,
            "apodo": profile_init_data.apodo or "",
            "frase": profile_init_data.frase or "",
            "objetivo": profile_init_data.objetivo or "",
            "titulo": "",
            "aura": "0",
            "mujeres": "",
            "img": "",
            "deuda": None,
        }
        
        profile_obj = Profile(**profile_dict)

        profile_doc = prepare_for_mongo(profile_obj.dict())
        
        profile_result = await db.profiles.insert_one(profile_doc)
        profile_id = profile_result.inserted_id

        if not profile_id:
            logger.error(f"Error inserting profile")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error inserting profile"
            )
        logger.info(f"Profile created for user {user.id}")

        await update_user_info(user, UpdateUser(is_active=True), db)
        logger.info(f"User marked as active successfully.")
        
        assignments_result = await create_assignments(user.id, user.name, db)
        assignments_id = assignments_result["assignment_id"]
        logger.info(f"Initial assignment created.")
    
        return EventResponse(
            profile_id=str(profile_id),
            assignments_id=assignments_id,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initialize profile:{type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting profile"
        )

async def update_the_profile_info(user_id: str, profile_info: ProfileUpdate, db) -> Profile:
    try:
        logger.info(f"Updating profile for user {user_id}")
        update_data = profile_info.dict(exclude_none=True)
        
        existing_profile = await db.profiles.find_one({"user_id": user_id})
        
        if not existing_profile:
            logger.error(f"Profile not found")
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Profile not found")

        result = await db.profiles.update_one(
            {"user_id": user_id}, 
            {"$set": update_data}
        )

        if result.modified_count > 0:
            logger.info(f"Profile updated successfully")
            profile_response = await db.profiles.find_one({"user_id": user_id})
        else:
            logger.info(f"No changes were made to the user profile.")
            profile_response = existing_profile

        return Profile(**parse_from_mongo(profile_response))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update profile error")