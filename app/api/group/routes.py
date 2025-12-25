from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.users.service import get_current_user, get_current_user_id
from app.database.database import get_database
from .schemas import Group,UpdateGroup,UpdateMembers,CreateGroup
from .service import update_members,update_group,create_group,delete_group_in_cascade,delete_group_by_id

router = APIRouter()

@router.post("/", response_model=Group)
async def create_new_group(group_data: CreateGroup,user_id=Depends(get_current_user_id), db=Depends(get_database)):
    result = await create_group(group_data, db)
    return result

@router.put("/{group_id}", response_model=Group)
async def update_group_by_id(group_id: str, update_data: UpdateGroup,user_id=Depends(get_current_user_id), db=Depends(get_database)):
    result = await update_group(group_id,update_data,db)
    return result

@router.put("/members/{group_id}", response_model=Group)
async def update_members_group(group_id: str, update_data: UpdateMembers,user_id=Depends(get_current_user_id), db=Depends(get_database)):
    result = await update_members(group_id, update_data,db)
    return result

@router.get("/", response_model=List[Group])
async def get_groups(db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    groups = await db.groups.find().to_list(100)
    return [Group(**group) for group in groups]

@router.get("/{group_id}", response_model=Group)
async def get_group_by_id(group_id: str, db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return Group(**group)

@router.delete("/{group_id}")
async def delete_group(group_id: str,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    return await delete_group_by_id(group_id,db)

@router.delete("/{group_id}/cascade")
async def delete_group_cascade(group_id: str,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    return await delete_group_in_cascade(group_id,db)