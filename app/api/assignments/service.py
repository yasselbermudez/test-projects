from fastapi import HTTPException,status
from app.database.database import prepare_for_mongo
from .schemas import AssignmentsMissionsResponse,Mission,Assignments, MissionType, ParamsUpdate,MissionStatus, ParamsUpdateVote
from app.api.missions.schemas import Mission as PrimaryMission
from datetime import datetime
import json
from ..history.schemas import Event
from ..history.service import create_event
from ..second_missions.service import create_secondary_mission

import logging
logger = logging.getLogger(__name__)

with open('./init_missions.json', 'r', encoding='utf-8') as f:
    missions = json.load(f)

async def get_assignments(person_id: str, db) -> Assignments:
    try:
        assignments = await db.assignments.find_one({"person_id":person_id})
        if not assignments:
            logger.error(f"No se encontro asignaciones para el usuario con id: {person_id}."),
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"No se encontro asignaciones para el usuario con id: {person_id}."
                )
        return Assignments(**assignments)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error obteniendo las asignaciones: ",str(e)),
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo las asignaciones"
        )


async def create_assignments(
    person_id: str,
    user_name: str,
    db,
) -> dict:
    try:
        
        mission_data = Mission(
            mission_id="1",
            mission_name=missions[0]["nombre"],  # Acceder como diccionario
            creation_date=datetime.now(),
            status = MissionStatus.ACTIVE
        )

        assignment = Assignments(
            person_id=person_id,
            person_name=user_name,
            mission=mission_data,
            secondary_mission=None,
            group_mission=None
        )
        
        assignment_doc = prepare_for_mongo(assignment.dict())
        result = await db.assignments.insert_one(assignment_doc)
        
        if not result.inserted_id:
            logger.error(f"Error al crear asignaciones para {person_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear asignaciones"
            )
        
        logger.info(f"Asignaciones creadas para usuario {person_id}")
        return {"assignment_id": str(result.inserted_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en creando assignacion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear asignacion"
        )

# eliminar sustituir o agregar una mision a la asignacion
async def update_assignments_missions(
    user_id: str, 
    type:MissionType,
    db
)->Assignments:
    try:
        # Verificar si la asignación existe
        existing_assignment = await db.assignments.find_one({"person_id": user_id})
        
        if not existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró asignación para el person_id: {user_id}",
            )

        # Preparar campos para actualización
        update_fields = {}
        
        if type==MissionType.SECONDARY:
            new_mission = await create_secondary_mission(user_id,db)

        elif type==MissionType.MAIN:
            mission_id = existing_assignment[type]["mission_id"]
            new_mission = await get_next_primary_mission(mission_id,db)
        
        mission_obj = Mission(
            mission_name=new_mission.nombre,
            mission_id=new_mission.id
        )   
    
        mission_doc = mission_obj.model_dump()
        # en este punto se genera:creation_date=datetime.datetime(2025, 11, 4, 11, 15, 18, 553625) que es convertido automaticamente por mongo 
        # # Convertir datetime a string ISO pero es recomendable cambiar al craar la asignacion a el formato {"$date": "..."} de mongo
        mission_doc["creation_date"] = mission_doc["creation_date"].isoformat()
        update_fields[type] = mission_doc

        # Ejecutar actualización
        result = await db.assignments.update_one(
            {"person_id": user_id},
            {"$set": update_fields}
        )
    
        if result.modified_count > 0:
            updated_assignment = await db.assignments.find_one({"person_id": user_id})
            logger.info("Mission actualizada exitosamente en la asignacion")
        else:
            updated_assignment = existing_assignment
            logger.info("No se realizaron cambios en las missiones de la asignacion")
        return Assignments(**updated_assignment)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error actualizando las misiones de la assignaciones: ",str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno sel servidor: {str(e)}")

#obtener los documentos de cada una de las misiones de las asignaciones
async def get_assignments_missions(person_id: str, db) -> AssignmentsMissionsResponse:
    try:
        assignments = await db.assignments.find_one({"person_id": person_id})
        
        if not assignments:
           logger.error(f"No se encontro asignaciones para el usuario con id: {person_id}.")
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND, 
               detail=f"No se encontro asignacion para el usuario con id: {person_id}."
               )
        
        assignments_obj = Assignments(**assignments)
        
        # Buscar secondary_mission si existe
        secondary_mission = None
        if (assignments_obj.secondary_mission and 
            assignments_obj.secondary_mission.mission_id):
            
            secondary_mission = await db.secondary.find_one({
                "id": assignments_obj.secondary_mission.mission_id
            })
        
        # Buscar mission principal si existe
        mission = None
        if (assignments_obj.mission and 
            assignments_obj.mission.mission_id):
            
            mission = await db.missions.find_one({
                "id": assignments_obj.mission.mission_id
            })

        response =  AssignmentsMissionsResponse(
            mission=mission,
            secondary_mission=secondary_mission
        )

        return response
    except HTTPException:    
        raise
    except Exception as e:
        logger.error("Error obteniendo las misiones de la assignaciones: ",str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno en el servidor: {str(e)}"
            )

# actualizar parametros parciales de misiones en las asignaciones 
async def update_missions_params(
    person_id: str, 
    update_data: ParamsUpdate, 
    db
)->Assignments:
    """
    Endpoint para actualizar parámetros específicos de una misión
    - Solo actualiza misiones existentes (no null)
    - Permite cambiar status,result,likes y dislikes
    """
    try:
        # Verificar si la asignación existe
        existing_assignment = await db.assignments.find_one({"person_id": person_id})
        
        if not existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Asignacion no encontrada"
                )

        # Verificar que la misión a actualizar existe y no es null
        mission_field = update_data.mission_type.value
        current_mission = existing_assignment.get(mission_field)
        
        if current_mission is None:
            logger.error(f"No se puede actualizar {mission_field} porque no existe")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se puede actualizar {mission_field} porque no existe",
            )

        # Preparar operaciones de actualización
        update_operations = {}
        provided_data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Manejar campos regulares (status, result) y like y dislike como regulares tambien
        set_updates = {}
        if "status" in provided_data:
            set_updates[f"{mission_field}.status"] = provided_data["status"]
        if "result" in provided_data:
            set_updates[f"{mission_field}.result"] = provided_data["result"]
        if "like" in provided_data:
            set_updates[f"{mission_field}.like"] = provided_data["like"]
        if "dislike" in provided_data:
            set_updates[f"{mission_field}.dislike"] = provided_data["dislike"]

        if set_updates:
            update_operations["$set"] = set_updates

        # Si no hay operaciones válidas
        if not update_operations:
            logger.error("No se proporcionaron parámetros válidos para actualizar")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No se proporcionaron parámetros válidos para actualizar",
            )
        
        # Ejecutar actualización
        result = await db.assignments.update_one(
            {"person_id": person_id},
            update_operations
        )

        if result.modified_count > 0:
            updated_assignment = await db.assignments.find_one({"person_id": person_id})
            logger.info("No se realizaron cambios en la asignacion")
        else:
            updated_assignment = existing_assignment
            logger.info("Asignacion actualizada exitosamente")
        return updated_assignment
        
    except Exception as e:
        logger.error("Error actualizando los parametros de la assignaciones: ",str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error actualizando los parametros: {str(e)}"
            )
    
async def update_missions_params_vote(
    user_id: str, 
    voter_id: str,
    update_data: ParamsUpdateVote, 
    db
)->Assignments:
    """
    Endpoint para actualizar parámetros específicos de una misión
    - Permite incrementar likes/dislikes solo si el coter no esta en la lista de voters
    - Comprueva si el numero de voters es igual al tamano del grupo y decide si la mission es aprobada o desaprobada
    """
    try:
        # Verificar si la asignación existe
        existing_assignment = await db.assignments.find_one({"person_id": user_id})
        
        if not existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                deatil=f"No se encontró asignación para el person_id: {user_id}",
            )
        
        # Verificar que la misión a actualizar existe y no es null
        mission_field = update_data.mission_type.value
        current_mission = existing_assignment.get(mission_field)
        

        if current_mission is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"No se puede actualizar {mission_field} porque no existe",
            )
        
        # comprobar si voto el usuario
        voters = current_mission["voters"]
        for voter in voters:
            if voter == voter_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El usuario: {voter_id} ya voto",
                )

        votesNeeded = update_data.group_size-1
    
        if len(voters)>=votesNeeded:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="La votacion esta llena",
            )
        #preparar la base de las operaciones de actualizacion
        update_operations = {}
        #provided_data = update_data.model_dump(exclude_unset=True, exclude_none=True)
        set_updates = {}

        #comprobamos si es el ultimo voto
        if len(voters)+1>=votesNeeded:
            
            # entonces este voto decide el resultado final de la mision
            like=current_mission["like"]
            dislike=current_mission["dislike"]

            if update_data.like:
                like+=1
            else:
                dislike+=1

            status_result = ""

            if like>=dislike:
                status_result = MissionStatus.COMPLETED
            else: status_result = MissionStatus.FAILED
            
            set_updates[f"{mission_field}.status"] = status_result
            update_operations["$set"] = set_updates
            #archivamos la mission
            await archive_result_mission(user_id,current_mission,mission_field,status_result,db)
            await add_mission_recompensa(user_id,current_mission,mission_field,status_result,db)
        else: 
            
            # Preparar operaciones de actualización de voto normales
            
            # Manejar campo votadores y sumar el nuevo votador
            
            newListUsers = voters + [voter_id]
            set_updates[f"{mission_field}.voters"] = newListUsers
            
            if set_updates:
                update_operations["$set"] = set_updates

            # Manejar incrementos (like, dislike)
            inc_updates = {}
            if  update_data.like:
                inc_updates[f"{mission_field}.like"] = 1
            else:
                inc_updates[f"{mission_field}.dislike"] = 1
            
            if inc_updates:
                update_operations["$inc"] = inc_updates

        
        # Si no hay operaciones válidas
        if not update_operations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No se proporcionaron parámetros válidos para actualizar",
            )
        
        # Ejecutar actualización
        result = await db.assignments.update_one(
            {"person_id": user_id},
            update_operations
        )
        
        if result.modified_count > 0:
            updated_assignment = await db.assignments.find_one({"person_id": user_id})
            logger.info("Parametros de voto actualizados exitosamente en la asignacion")
        else:
            updated_assignment = existing_assignment
            logger.info("No se realizaron cambios en los parametros de votos de la asignacion")
        return Assignments(**updated_assignment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando el voto: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando el voto",
        )
    
async def archive_result_mission(user_id:str,current_mission:dict,mission_field:MissionType,status_result:str,db):
    # preparamos la mission para archivarla en un envento de la historia
    try:
        current_mission_obj:Mission = Mission(**current_mission)

        if mission_field==MissionType.MAIN:
            mission_details = await db.missions.find_one({"id":current_mission_obj.mission_id})
            logro = mission_details["logro"]
            if logro : logro_name = logro["nombre"]
            else: logro_name = None
        else: logro_name = None

        event_data = Event(
            user_id=user_id,
            mission_id=current_mission_obj.mission_id,
            result=current_mission_obj.result,
            tipo=mission_field,
            name=current_mission_obj.mission_name,
            status=status_result,
            logro_name=logro_name
        )
        
        await create_event(event_data,db)
    except HTTPException:
        raise
    except Exception as e:
        raise

async def add_mission_recompensa(user_id:str,current_mission:dict,mission_field:str,status_result:str,db):
    # procesamos la recompensa en base al resultado de la mision
    try:
        current_mission_obj:Mission = Mission(**current_mission)
        mission_id=current_mission_obj.mission_id
        
        if mission_field==MissionType.MAIN:
            mission_details = await db.missions.find_one({"id":mission_id})
        else: 
            mission_details = await db.secondary.find_one({"id":mission_id})
       
        recompensa = mission_details["recompensa"]
        recompensa_int = int(recompensa)

        if status_result == MissionStatus.FAILED:
            recompensa_int = - recompensa_int
 
        user_profile_data = await db.profiles.find_one({"user_id":user_id})
        user_score = user_profile_data["aura"]
        user_score_int = int(user_score)

        update_score = user_score_int + recompensa_int

        update_data = {
            "aura":str(update_score)
        }
        result = await db.profiles.update_one(
                {"user_id": user_id}, 
                {"$set": update_data}
            )
        if not result.matched_count > 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"No se pudo registrar la recompensa",
            )
        logger.info(f"Recompensa registrada para el user_id:{user_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando la recompensa: {type(e).__name__}: {e}")
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error procesando la recompensa",
            )
    

async def get_next_primary_mission(mission_id:str,db)->PrimaryMission:
    try:
        mission_id_int = int(mission_id)
        next_mission_id = str(mission_id_int+1)
        next_mission = await db.missions.find_one({"id": next_mission_id})
        if not next_mission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontro la siguiente mision principal",
            )
        return PrimaryMission(**next_mission)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo siguiente mision principal: {type(e).__name__}: {e}")
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo siguiente mision principal",
            )