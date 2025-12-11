from fastapi import APIRouter, Depends
from app.api.users.service import get_current_user_id
from app.database.database import get_database
from .schemas import EventResponse,SecondaryMission
from .service import create_secondary_mission

router = APIRouter()

@router.get("/",response_model = list[SecondaryMission])
async def get_missions(db=Depends(get_database)):
    missions = await db.secondary.find().to_list(100)
    return [SecondaryMission(**mission) for mission in missions]

@router.post("/",response_model = EventResponse)
async def create_secondary(user_id:str=Depends(get_current_user_id),db=Depends(get_database)) :
    result = await create_secondary_mission(user_id,db)
    return result


