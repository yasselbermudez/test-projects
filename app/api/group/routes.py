from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.users.service import get_current_user_id
from app.database.database import get_database
from .schemas import Group,UpdateGroup,UpdateMembers,CreateGroup
from .service import update_members,update_group,create_group,delete_group_in_cascade,delete_group_by_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=Group)
async def create_new_group(group_data: CreateGroup,user_id=Depends(get_current_user_id), db=Depends(get_database)):
    return await create_group(group_data, db)
    

@router.put("/{group_id}", response_model=Group)
async def update_group_by_id(group_id: str, update_data: UpdateGroup,user_id=Depends(get_current_user_id), db=Depends(get_database)):
    return await update_group(group_id,update_data,db)
   

@router.put("/members/{group_id}", response_model=Group)
async def update_members_group(group_id: str, update_data: UpdateMembers,user_id=Depends(get_current_user_id), db=Depends(get_database)):
    return await update_members(group_id, update_data,db)
    

@router.get("", response_model=List[Group])
async def get_groups(db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    try:
        logger.info("Retrieving all groups")
        groups = await db.groups.find().to_list(100)
        if not groups:
            logger.error("No groups found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No groups found")
        return [Group(**group) for group in groups]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving groups: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving groups")

@router.get("/{group_id}", response_model=Group)
async def get_group_by_id(group_id: str, db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    try:
        logger.info(f"Retrieving group with id: {group_id}")
        group = await db.groups.find_one({"id": group_id})
        if not group:
            logger.error(f"Group not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        return Group(**group)
    except HTTPException:
        raise   
    except Exception as e:
        logger.error(f"Error retrieving group {group_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving group")

@router.delete("/{group_id}")
async def delete_group(group_id: str,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    return await delete_group_by_id(group_id,db)

@router.delete("/{group_id}/cascade")
async def delete_group_cascade(group_id: str,user_id:str=Depends(get_current_user_id),db=Depends(get_database)):
    return await delete_group_in_cascade(group_id,db)