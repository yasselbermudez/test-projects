from datetime import datetime
from fastapi import  HTTPException,status
from .schemas import Group,Member, UpdateGroup,UpdateMembers,CreateGroup
import logging

logger = logging.getLogger(__name__)

async def create_group(group_data: CreateGroup, db) -> Group:
    try:
        logger.info("Init create group")
        creator_member = Member(user_id=group_data.current_user_id, user_name=group_data.current_user_name)

        new_group = Group(
            group_name=group_data.group_name,
            members=[creator_member],
            created=datetime.now(),
            created_by=group_data.current_user_name,
            creator_id=group_data.current_user_id,
            password=group_data.password
        )
        
        result = await db.groups.insert_one(new_group.dict())

        if not result.inserted_id:
            logger.error("The group could not be created")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="The group could not be created")
        
        logger.info(f"Created group with id:{str(result.inserted_id)}")
        
        update_result = await db.users.update_one(
            {"id": group_data.current_user_id}, 
            {"$set": {"group_id": new_group.id}}
        )

        if update_result.modified_count == 0:
            logger.error("Group created but user not updated")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Grupo creado pero usuario no actualizado")
        
        return new_group
         
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group {str(e)}") 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating group {str(e)}")
    

async def update_members(group_id: str, update_data: UpdateMembers, db):
    try:
        logger.info("Init Update group member")
        
        existing_group = await db.groups.find_one({"id": group_id})
        if not existing_group:
            logger.error("Group not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        group = Group(**existing_group)

        # Delete member
        if update_data.remove:
            
            if update_data.user_id == group.creator_id:
                logger.error("The group creator cannot be removed")
                raise HTTPException(status_code=400, detail="The group creator cannot be removed")
            
            member_exists = any(member.user_id == update_data.user_id for member in group.members)
            if not member_exists:
                logger.error("User does not exist in the group")
                raise HTTPException(status_code=404, detail="User does not exist in the group")
            
            # Exclude member
            updated_members = [member for member in group.members if member.user_id != update_data.user_id]
            new_group = None
        
        # Add member
        else:
            # No more than 5 members
            if len(group.members) >= 5:
                logger.error("The group cannot contain more than 5 members")
                raise HTTPException(status_code=400, detail="The group cannot contain more than 5 members")
            
            # Verify that the user is not already in the group
            member_exists = any(member.user_id == update_data.user_id for member in group.members)
            if member_exists:
                logger.error("The user is already a member of the group")
                raise HTTPException(status_code=400, detail="The user is already a member of the group")
            
            # Add new member
            new_member = Member(user_id=update_data.user_id, user_name=update_data.user_name)
            updated_members = group.members + [new_member]
            new_group = group_id
        
        group_update_result = await db.groups.update_one(
            {"id": group_id}, 
            {"$set": {"members": [member.dict() for member in updated_members]}}
        )
        if group_update_result.modified_count == 0:
            logger.error("The group could not be updated")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="The group could not be updated")
        
        # Update user group information
        user_update_result = await db.users.update_one(
            {"id": update_data.user_id}, 
            {"$set": {"group_id": new_group}}
        )
        if user_update_result.modified_count == 0:
            logger.error("Group upadted but user not updated")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Group upadted but user not updated")
        
        updated_group = await db.groups.find_one({"id": group_id})
        logger.info("Updated group members succes")
        return Group(**updated_group)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group members: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating group members: {str(e)}")

async def update_group(group_id: str, update_data: UpdateGroup, db):
    try:
        logger.info("Init update group")
        existing_group = await db.groups.find_one({"id": group_id})
        if not existing_group:
            logger.error("Group not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
        group = Group(**existing_group)
        update_dict = {}
        
        
        if update_data.members:
            # 5 members max
            if len(update_data.members) > 5:
                logger.error("The group is full.")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The group is full.")
            
            # The creator remains
            creator_still_member = any(member.user_id == group.creator_id for member in update_data.members)
            if not creator_still_member:
                logger.error("The group creator must remain a member")
                raise HTTPException(status_code=400, detail="The group creator must remain a member")
            
            update_dict["members"] = [member.dict() for member in update_data.members]
        
        if update_dict:
            result  = await db.groups.update_one({"id": group_id}, {"$set": update_dict})
        
        if result.modified_count == 0:
            response_group = existing_group
            logger.error("The group could not be updated")
        else:
            updated_group = await db.groups.find_one({"id": group_id})
            response_group = Group(**updated_group)
            logger.info(f"Group {group_id} updated successfully")

        return response_group
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el grupo")

async def delete_group_by_id(group_id: str,db):
    try:
        logger.info(f"Init delete group by id: {group_id}")
        
        result = await db.groups.delete_one({"id": group_id})
        
        if result.deleted_count == 0:
            logger.error("Grupo not found")
            raise HTTPException(status_code=404, detail="Grupo not found")
        
        return True    
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting group")

async def delete_group_in_cascade(group_id: str,db):
    try:
        logger.info(f"Init delete group in cascade: {group_id}")
        group = await db.groups.find_one({"id": group_id})
        group_obj = Group(**group)
        group_size = len(group_obj.members)
        
        if not group:
            logger.error("Grupo not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo not found")
        
        delete_result = await db.groups.delete_one({"id": group_id})
        
        if delete_result.deleted_count != 1:
            logger.error("Error deleting group")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el grupo")
        
        update_result = await db.users.update_many(
            {"group_id": group_id},
            {"$set": {"group_id": None}}
        )

        if update_result.modified_count != group_size:
            logger.error("Group deleted but not all users were updated")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Group deleted but not all users were updated")

        logger.info("Group and associated users updated successfully")
        return True

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cascading deletion: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in cascading deletion")