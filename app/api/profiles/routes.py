from fastapi import APIRouter, Depends, HTTPException,status
from app.api.assignments.service import create_assignments
from app.api.auth.schemas import User
from app.api.users.schemas import UpdateUser
from app.api.users.service import get_current_user, get_current_user_id, update_user_info
from app.database.database import get_database
from .schemas import Profile, ProfileInit, ProfileUpdate
from .service import initialize_profile_data
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/groups/{group_id}",response_model = list[Profile])
async def get_profiles_data(group_id:str,db=Depends(get_database),user_id:str=Depends(get_current_user_id)):
    group = await db.groups.find_one({"id":group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    members = group["members"]
    user_ids = [member["user_id"] for member in members]

    profiles = await db.profiles.find({"user_id": {"$in": user_ids}}).to_list(len(members))
    return [Profile(**profile) for profile in profiles]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def initialize_profile(
    profile_init_data: ProfileInit,
    user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    
    try:
        await initialize_profile_data(user.id, user.email, user.name, profile_init_data, db)
        logger.info(f"Perfil inicializado para usuario {user.email}")
        
        await update_user_info(user.id, UpdateUser(is_active=True), db)
        logger.info(f"Usuario {user.email} marcado como activo")
        
        await create_assignments(user.id, user.name, db)
        logger.info(f"Tareas iniciales creadas para usuario {user.email}")
        
        return {
            "message": f"Perfil para {user.name} inicializado exitosamente",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error no manejado en initialize_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.get("/",response_model = Profile)
async def get_profile(user_id:str=Depends(get_current_user_id),db=Depends(get_database)) -> Profile:
    result = await db.profiles.find_one({"user_id": user_id})
    if not result:
        return HTTPException(status_code=404,detail="Profile not found")
    return result


@router.put("/",response_model=Profile) 
async def update_profile_info(profile_info: ProfileUpdate,user_id:str=Depends(get_current_user_id), db=Depends(get_database)):
    try:
        update_data = profile_info.dict(exclude_none=True)
        
        existing_profile = await db.profiles.find_one({"user_id": user_id})
        
        if not existing_profile:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Profile not found")

        result = await db.profiles.update_one(
            {"user_id": user_id}, 
            {"$set": update_data}
        )

        if result.modified_count > 0:
            logger.info(f"perfil del usuario:{user_id} actualizado exitosamente")
            profile_response = db.profiles.find_one({"user_id": user_id})
        else:
            logger.info(f"No se realizaron cambios en el perfil del usuario {user_id}")
            profile_response = existing_profile
        
        return profile_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error durante la actualizacion: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update error")
    

