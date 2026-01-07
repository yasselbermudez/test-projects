from fastapi import HTTPException,status
from app.api.group.schemas import Group
from .schemas import Event, History
from app.database.database import prepare_for_mongo
import logging
logger = logging.getLogger(__name__)

async def create_event(event_data: Event, db) -> str:
    try:
        logger.info(f"Creating event for user: {event_data.user_id}")

        event_data_doc = prepare_for_mongo(event_data.dict())
        
        result = await db.history.insert_one(event_data_doc)
        
        if not result.inserted_id:
            logger.error("Failed to create event: No inserted_id returned")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Failed to create event: No inserted_id returned",
            )
        return str(result.inserted_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inserting event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting event: {e}"
        )
    
async def get_group_history(group_id,db)->list[History]:
    try:
        logger.info(f"Fetching history for group: {group_id}")
        group = await db.groups.find_one({"id": group_id})
        if not group:
            logger.error(f"Group not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        group = Group(**group)
        members = group.members

        history_list = []

        for member in members:
            events_cursor = db.history.find({"user_id": member.user_id}).limit(100)
            events = await events_cursor.to_list(length=100)
            event_objects = [Event(**event) for event in events]
            
            history = History(
                user_name=member.user_name,
                events=event_objects
            )
            history_list.append(history)

        return history_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting the group history:{type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting the group history"
        )
