from fastapi import APIRouter, Depends, HTTPException
from app.api.users.service import get_current_user_id
from app.database.database import get_database
from .schemas import Logro, Mission
from .service import initialize_logros, initialize_missions
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=list[Mission])
async def get_all_missions(db=Depends(get_database),user_id: str = Depends(get_current_user_id)):
    try:
        logger.info("Retrieving all missions")
        missions = await db.missions.find().to_list(100)
        if not missions :
            logger.error("No missions found")
            raise HTTPException(status_code=404, detail="No missions found")
        return [Mission(**mission) for mission in missions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving missions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving missions")

@router.get("/logros", response_model=list[Logro])
async def get_missions_logros(db=Depends(get_database),user_id: str = Depends(get_current_user_id)):
    try:
        logger.info("Retrieving all logros")
        logros = await db.logros.find().to_list(100)
        if not logros:
            logger.error("No logros found")
            raise HTTPException(status_code=404, detail="No logros found")
        return [Logro(**logro) for logro in logros]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving logros: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logros: {str(e)}")

@router.get("/{mission_id}", response_model=Mission)
async def get_mission(mission_id: str, db=Depends(get_database),user_id: str = Depends(get_current_user_id)):
    try:
        logger.info(f"Retrieving mission with ID: {mission_id}")
        mission = await db.missions.find_one({"id": mission_id})
        if mission is None:
            logger.error(f"Mission not found")
            raise HTTPException(status_code=404, detail="Mission not found")
        return Mission(**mission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mission: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving mission: {str(e)}")

@router.post("/init-data",response_model=dict)
async def initialize_missions_data(db=Depends(get_database),user_id: str = Depends(get_current_user_id)):
    resultMissions = await initialize_missions(db)
    resultLogros = await initialize_logros(db)
    return {"message": f"Initialized {resultMissions} missions and {resultLogros} logros."}