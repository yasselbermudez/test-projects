from fastapi import APIRouter, Depends,HTTPException
from app.api.users.service import get_current_user_id
from app.database.database import get_database
from .schemas import SecondaryMission
from .service import create_secondary_mission

router = APIRouter()

@router.get("/",response_model = list[SecondaryMission])
async def get_missions(user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    try:
        missions = await db.secondary.find().to_list(100)
        if not missions:
            raise HTTPException(status_code=404, detail="No secondary missions found")
        return [SecondaryMission(**mission) for mission in missions]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving secondary missions")

@router.post("/",response_model = SecondaryMission)
async def create_secondary(user_id:str=Depends(get_current_user_id),db=Depends(get_database)) :
    return await create_secondary_mission(user_id,db)


