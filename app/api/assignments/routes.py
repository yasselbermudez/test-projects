from typing import Optional
from fastapi import APIRouter, Depends
from app.api.auth.schemas import User
from app.api.users.service import get_current_user, get_current_user_id
from app.database.database import get_database
from .schemas import AssignmentsMissionsResponse,Assignments, MissionType,ParamsUpdate,ParamsUpdateVote
from .service import get_assignments,get_assignments_missions,create_assignments,update_assignments_missions,update_missions_params,update_missions_params_vote

router = APIRouter()

@router.get("/{person_id}",response_model = Assignments)
async def get_one_assignments(person_id:str,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    return await get_assignments(person_id,db)
  
@router.get("/{person_id}/missions",response_model = AssignmentsMissionsResponse)
async def get_assignments_all_mission(person_id:str,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    return await get_assignments_missions(person_id,db)

@router.post("/",response_model = dict)
async def create_new_assignments(user:User=Depends(get_current_user),db=Depends(get_database)):
    return await create_assignments(user.id,user.name,db)
     
@router.put("/missions/params",response_model = Assignments)
async def update_assignments_missions_params(update_data: ParamsUpdate,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    return await update_missions_params(user_id,update_data,db)

@router.put("/missions/{type}",response_model = Assignments)
async def update_assignments_one_missions(type:MissionType,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    return await update_assignments_missions(user_id,type,db)
     
@router.put("/{user_id}/missions/votes",response_model = Assignments)
async def update_assignments_missions_params_vote(user_id:str,update_data: ParamsUpdateVote,voter_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    return await update_missions_params_vote(user_id,voter_id,update_data,db)




