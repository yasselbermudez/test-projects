from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_database
from .schemas import AssignmentsMissionsResponse,Assignments,Mission,EventResponse, MissionType,ParamsUpdate,UpdateAssignments,ParamsUpdateVote
from .services import get_assignments_missions,create_assignments,update_assignments_missions,update_assignments_missions_params,missions_params_vote

router = APIRouter()

@router.get("/{person_id}",response_model = Assignments)
async def get_assignments(person_id:str,db=Depends(get_database)):
    assignments = await db.assignments.find_one({"person_id":person_id})
    return Assignments(**assignments)

@router.get("/{person_id}/missions",response_model = AssignmentsMissionsResponse)
async def get_assignments_all_mission(person_id:str,db=Depends(get_database)):
    return await get_assignments_missions(person_id,db)

@router.post("/{person_id}",response_model = EventResponse)
async def create_new_assignments(person_id:str,user_name:str,mission_data:Optional[Mission]=None,db=Depends(get_database)):
    result = await create_assignments(person_id,user_name,db,mission_data)
    return result

@router.put("/{person_id}/missions/params",response_model = EventResponse)
async def Update_assignments_missions_params(person_id:str,update_data: ParamsUpdate,db=Depends(get_database)):
    result = await update_assignments_missions_params(person_id,update_data,db)
    return result

@router.put("/{person_id}/missions/{type}",response_model = EventResponse)
async def Update_assignments_missions(person_id:str,type:MissionType,db=Depends(get_database)):
    result = await update_assignments_missions(person_id,type,db)
    return result

@router.put("/{person_id}/missions/votes/{voter_id}",response_model = EventResponse)
async def Update_assignments_missions_params_vote(person_id:str,voter_id:str,update_data: ParamsUpdateVote,db=Depends(get_database)):
    result = await missions_params_vote(person_id,voter_id,update_data,db)
    return result
