from fastapi import APIRouter, Depends,HTTPException
from app.api.users.service import get_current_user_id
from app.database.database import get_database
from .schemas import SecondaryMission
from .service import create_secondary_mission
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("",response_model = list[SecondaryMission])
async def get_missions(user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    try:
        logger.info("Get all the secondary missions")
        missions = await db.secondary.find().to_list(100)
        if not missions:
            logger.info("No secondary missions found")
            raise HTTPException(status_code=404, detail="No secondary missions found")
        
        return [SecondaryMission(**mission) for mission in missions]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving secondary missions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving secondary missions: {str(e)}")

@router.post("",response_model = SecondaryMission)
async def create_secondary(user_id:str=Depends(get_current_user_id),db=Depends(get_database)) :
    return await create_secondary_mission(user_id,db)


