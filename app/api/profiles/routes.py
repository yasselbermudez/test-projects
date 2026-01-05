from fastapi import APIRouter, Depends, HTTPException,status
from app.api.auth.schemas import User
from app.api.users.service import get_current_user, get_current_user_id
from app.database.database import get_database, parse_from_mongo
from .schemas import EventResponse, Profile, ProfileInit, ProfileUpdate
from .service import initialize_profile_data, update_the_profile_info
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("",response_model = Profile)
async def get_profile(user_id:str=Depends(get_current_user_id),db=Depends(get_database)) -> Profile:
    try:
        logger.info(f"Retrieving profile for user {user_id}")
        result = await db.profiles.find_one({"user_id": user_id})
        if not result:
            logger.error("Profile not found")
            raise HTTPException(status_code=404,detail="Profile not found")
        return Profile(**parse_from_mongo(result))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile for user: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error retrieving profile"
        )

@router.post("", response_model=EventResponse)
async def initialize_profile(profile_init_data: ProfileInit,user: User = Depends(get_current_user),db = Depends(get_database)):
    return await initialize_profile_data(user, profile_init_data, db)
        
@router.put("",response_model=Profile) 
async def update_profile_info(profile_info: ProfileUpdate,user_id:str=Depends(get_current_user_id), db=Depends(get_database)):
    return await update_the_profile_info(user_id, profile_info, db)
    
@router.get("/groups/{group_id}",response_model = list[Profile])
async def get_profiles_data(group_id:str,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    try:
        logger.info(f"Retrieving profiles for group {group_id}")
        group = await db.groups.find_one({"id":group_id})
        if not group:
            logger.error("Group not found")
            raise HTTPException(status_code=404, detail="Group not found")
        members = group["members"]
        user_ids = [member["user_id"] for member in members]

        profiles = await db.profiles.find({"user_id": {"$in": user_ids}}).to_list(len(members))
        return [Profile(**profile) for profile in profiles]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profiles data: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving profiles data")
    

