from fastapi import APIRouter, Depends, HTTPException
from app.api.group.schemas import Group
from app.api.users.service import get_current_user_id
from app.database.database import get_database
from .schemas import Event, EventResponse, History
from .service import create_event

router = APIRouter()

@router.post("/events/", response_model=EventResponse)
async def create_event_history(event_data: Event,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    result = await create_event(event_data, db)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result

@router.get("/", response_model=list[Event])
async def get_event_history(user_id:str=Depends(get_current_user_id), db=Depends(get_database)):
    events = await db.history.find({"user_id": user_id}).to_list(100)
    if not events:
        raise HTTPException(status_code=404, detail="Events not found")
    return [Event(**event) for event in events]


@router.get("/group/{group_id}",response_model = list[History])
async def get_profiles_data(group_id:str,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    
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