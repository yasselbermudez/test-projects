from fastapi import APIRouter, Depends
from app.database.database import get_database
from .schemas import EventResponse,SecondaryMission
from .service import create_secondary_mission

router = APIRouter()

@router.get("/",response_model = list[SecondaryMission])
async def get_missions(db=Depends(get_database)):
    missions = await db.secondary.find().to_list(100)
    return [SecondaryMission(**mission) for mission in missions]

@router.post("/{person_id}",response_model = EventResponse)
async def create_secondary(person_id: str,db=Depends(get_database)) :
    result = await create_secondary_mission(person_id,db)
    return result


