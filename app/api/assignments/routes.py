from fastapi import APIRouter, Depends
from app.api.auth.schemas import User
from app.api.users.service import get_current_user, get_current_user_id
from app.database.database import get_database
from .schemas import AssignmentsMissionsResponse,Assignments,EventResponse, MissionType,ParamsUpdate,ParamsUpdateVote
from .services import get_assignments_missions,create_assignments,update_assignments_missions,update_assignments_missions_params,missions_params_vote

router = APIRouter()

@router.get("/{user_id}",response_model = Assignments)
async def get_assignments(user_id:str,db=Depends(get_database)):
    assignments = await db.assignments.find_one({"person_id":user_id})
    return Assignments(**assignments)

@router.get("/{user_id}/missions",response_model = AssignmentsMissionsResponse)
async def get_assignments_all_mission(user_id:str,db=Depends(get_database)):
    return await get_assignments_missions(user_id,db)

@router.post("/",response_model = EventResponse)
async def create_new_assignments(user:User=Depends(get_current_user),db=Depends(get_database)):
    result = await create_assignments(user.id,user.name,db)
    return result

@router.put("/missions/params",response_model = EventResponse)
async def Update_assignments_missions_params(update_data: ParamsUpdate,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    result = await update_assignments_missions_params(user_id,update_data,db)
    return result

@router.put("/missions/{type}",response_model = EventResponse)
async def Update_assignments_missions(type:MissionType,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    result = await update_assignments_missions(user_id,type,db)
    return result

@router.put("{user_id}/missions/votes",response_model = EventResponse)
async def Update_assignments_missions_params_vote(user_id:str,update_data: ParamsUpdateVote,voter_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    result = await missions_params_vote(user_id,voter_id,update_data,db)
    return result




