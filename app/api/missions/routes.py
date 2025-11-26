from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_database
from .schemas import Logro, Mission, EventResponse
from .service import initialize_logros, initialize_missions

router = APIRouter()

@router.get("/", response_model=list[Mission])
async def get_all_missions(db=Depends(get_database)):
    missions = await db.missions.find().to_list(100)
    return [Mission(**mission) for mission in missions]

@router.get("/logros", response_model=list[Logro])
async def get_missions_logros(db=Depends(get_database)):
    logros = await db.logros.find().to_list(100)
    return [Logro(**logro) for logro in logros]

@router.get("/{mission_id}", response_model=Mission)
async def get_mission(mission_id: str, db=Depends(get_database)):
    mission = await db.missions.find_one({"id": mission_id})
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return Mission(**mission)

@router.post("/init-data")
async def initialize_missions_data(db=Depends(get_database)):
    resultMissions = await initialize_missions(db)
    resultLogros = await initialize_logros(db)
    return {"missions": resultMissions, "logros": resultLogros}