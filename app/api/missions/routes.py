from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_database
from .schemas import Logro, Mission, EventResponse
from .service import initialize_logros, initialize_missions

router = APIRouter()

@router.get("/", response_model=list[Mission])
async def get_all_missions(db=Depends(get_database)):
    try:
        missions = await db.missions.find().to_list(100)
        return [Mission(**mission) for mission in missions]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving missions")

@router.get("/logros", response_model=list[Logro])
async def get_missions_logros(db=Depends(get_database)):
    try:
        logros = await db.logros.find().to_list(100)
        return [Logro(**logro) for logro in logros]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving logros")

@router.get("/{mission_id}", response_model=Mission)
async def get_mission(mission_id: str, db=Depends(get_database)):
    try:
        mission = await db.missions.find_one({"id": mission_id})
        if mission is None:
            raise HTTPException(status_code=404, detail="Mission not found")
        return Mission(**mission)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving mission")

@router.post("/init-data",response_model=dict)
async def initialize_missions_data(db=Depends(get_database)):
    resultMissions = await initialize_missions(db)
    resultLogros = await initialize_logros(db)
    return {"message": f"Initialized {resultMissions} missions and {resultLogros} logros."}