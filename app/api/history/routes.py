from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_database
from .schemas import Event, EventResponse
from .service import create_event

router = APIRouter()

@router.post("/events/", response_model=EventResponse)
async def create_event_history(event_data: Event,db=Depends(get_database)):
    result = await create_event(event_data, db)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result

@router.get("/{user_id}", response_model=list[Event])
async def get_event_history(user_id: str, db=Depends(get_database)):
    events = await db.history.find({"user_id": user_id}).to_list(100)
    if not events:
        raise HTTPException(status_code=404, detail="Events not found")
    return [Event(**event) for event in events]