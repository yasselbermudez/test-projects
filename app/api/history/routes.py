from fastapi import APIRouter, Depends, HTTPException,status
from app.api.users.service import get_current_user_id
from app.database.database import get_database
from .schemas import Event, History
from .service import create_event, get_group_history
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/events/", response_model=str)
async def create_event_history(event_data: Event,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    return await create_event(event_data, db)

@router.get("", response_model=list[Event])
async def get_event_history(user_id:str=Depends(get_current_user_id), db=Depends(get_database)):
    try:
        logger.info(f"Retrieving events for user: {user_id}")
        events = await db.history.find({"user_id": user_id}).to_list(100)
        if not events:
            logger.error(f"Events not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Events not found")
        return [Event(**event) for event in events]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving events: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving events")

@router.get("/group/{group_id}",response_model = list[History])
async def get_profiles_data(group_id:str,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    return await get_group_history(group_id,db)
    