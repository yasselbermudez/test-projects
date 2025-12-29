from fastapi import HTTPException,status
from app.api.group.schemas import Group
from .schemas import Event, History
from app.database.database import prepare_for_mongo
import logging
logger = logging.getLogger(__name__)

async def create_event(event_data: Event, db) -> str:
    try:
        # Conversión directa 
        event_data_doc = prepare_for_mongo(event_data.dict())
        
        result = await db.history.insert_one(event_data_doc)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No se pudo crear el evento",
            )
        return str(result.inserted_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear evento"
        )
    
async def get_group_history(group_id,db)->list[History]:
    try:
        group = await db.groups.find_one({"id": group_id})
        if not group:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
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
        logger.error(f"Error obteniendo el historial del grupo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo el historial del grupo"
        )
