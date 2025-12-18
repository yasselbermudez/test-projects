from app.api.errors import ERROR_CODES
from .schemas import Profile, ProfileInit
from app.database.database import prepare_for_mongo
from fastapi import HTTPException,status
import logging

logger = logging.getLogger(__name__)

async def initialize_profile_data(
    user_id: str, 
    email: str, 
    name: str, 
    profile_init_data: ProfileInit, 
    db
):
    
    try:
        existing_profile = await db.profiles.find_one({"user_id": user_id})
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El perfil para el usuario {email} ya existe"
            )

        # 2. Preparar datos del perfil
        profile_dict = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "edad": profile_init_data.edad,
            "estatura": profile_init_data.estatura,
            "peso_corporal": profile_init_data.peso_corporal,
            "pesos": profile_init_data.pesos,
            "apodo": profile_init_data.apodo or "",
            "frase": profile_init_data.frase or "",
            "objetivo": profile_init_data.objetivo or "",
            "titulo": "",
            "aura": "0",
            "mujeres": "",
            "img": "",
            "deuda": None,
        }
        
        profile_obj = Profile(**profile_dict)

        profile_doc = prepare_for_mongo(profile_obj.dict())
        
        result = await db.profiles.insert_one(profile_doc)
        
        if not result.inserted_id:
            logger.error(f"Error al insertar perfil para usuario {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al guardar el perfil"
            )
        
        logger.info(f"Perfil creado para usuario {user_id}")
        return {"profile_id": str(result.inserted_id)}
        
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
    except Exception as e:
        logger.error(f"Error en initialize_profile_data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el perfil"
        )