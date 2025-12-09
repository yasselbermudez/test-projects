from typing import Optional
from fastapi import HTTPException
from app.database.database import prepare_for_mongo
from .schemas import AssignmentsMissionsResponse,EventResponse,Mission,Assignments, MissionType, ParamsUpdate,MissionStatus, ParamsUpdateVote
from datetime import datetime
import json

from ..history.schemas import Event
from ..history.service import create_event

from ..second_missions.service import create_secondary_mission
from ..second_missions.schemas import EventResponse as CreateMissionResponse

with open('./init_missions.json', 'r', encoding='utf-8') as f:
    missions = json.load(f)

async def create_assignments(
    person_id: str,
    user_name: str,
    db,
) -> EventResponse:
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
        
        return EventResponse(
                id=str(result.inserted_id),
                message="Assignment created successfully",
                success=True
            )
    
    except Exception as e:
        return EventResponse(
                id="",
                message=f"Error creando la asignacion: {str(e)}",
                success=False
            )

# eliminar sustituir o agregar una mision a la asignacion
async def update_assignments_missions(
    user_id: str, 
    type:MissionType,
    db
):
    try:
        # Verificar si la asignación existe
        existing_assignment = await db.assignments.find_one({"person_id": user_id})
        
        if not existing_assignment:
            return EventResponse(
                id=user_id,
                message=f"No se encontró asignación para el person_id: {user_id}",
                success=False
            )

        # Preparar campos para actualización
        update_fields = {}
        
        if type==MissionType.SECONDARY:
            # preparar la nueva misión
            new_mission = await create_secondary_mission(user_id,db)
            
            if not new_mission.success:
                return EventResponse(
                id=user_id,
                message="No se pudo generar la mision secundaria",
                success=False
            )

        elif type==MissionType.MAIN:
            mission_id = existing_assignment[type]["mission_id"]
            new_mission = await get_next_primary_mission(mission_id,db)
            
            if not new_mission.success:
            
                return EventResponse(
                id=user_id,
                message="No se pudo encontrar la mision principal",
                success=False
            )

        mission_obj = Mission(
            mission_name=new_mission.mission_name,
            mission_id=new_mission.mission_id
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
            return EventResponse(
                id=user_id,
                message="Misiones actualizadas exitosamente",
                success=True
            )
        else:
            return EventResponse(
                id=user_id,
                message="No se realizaron cambios en las misiones",
                success=True
            )
    
    except Exception as e:
        print("ocurrio un error: ",str(e))
        return EventResponse(
            id=user_id,
            message=f"Error actualizando las misiones: {str(e)}",
            success=False
        )

#obtener los documentos de cada una de las misiones de las asignaciones
async def get_assignments_missions(person_id: str, db) -> AssignmentsMissionsResponse:
    try:
        assignments = await db.assignments.find_one({"person_id": person_id})
        
        if not assignments:
           raise HTTPException(status_code=404, detail="Asignacion no encontrada")
        
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
        
    except Exception as e:
        print(f"Error en get_assignments_missions: {e}")
        return AssignmentsMissionsResponse()

# actualizar parametros parciales de misiones en las asignaciones 
async def update_assignments_missions_params(
    person_id: str, 
    update_data: ParamsUpdate, 
    db
):
    """
    Endpoint para actualizar parámetros específicos de una misión
    - Solo actualiza misiones existentes (no null)
    - Permite incrementar likes/dislikes
    - Permite cambiar status y result
    """
    try:
        # Verificar si la asignación existe
        existing_assignment = await db.assignments.find_one({"person_id": person_id})
        
        if not existing_assignment:
            return EventResponse(
                id=person_id,
                message=f"No se encontró asignación para el person_id: {person_id}",
                success=False
            )

        # Verificar que la misión a actualizar existe y no es null
        mission_field = update_data.mission_type.value
        current_mission = existing_assignment.get(mission_field)
        
        if current_mission is None:
            return EventResponse(
                id=person_id,
                message=f"No se puede actualizar {mission_field} porque no existe",
                success=False
            )

        # Preparar operaciones de actualización
        update_operations = {}
        provided_data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Manejar campos regulares (status, result)
        set_updates = {}
        if "status" in provided_data:
            set_updates[f"{mission_field}.status"] = provided_data["status"]
        if "result" in provided_data:
            set_updates[f"{mission_field}.result"] = provided_data["result"]
        
        if set_updates:
            update_operations["$set"] = set_updates

        # Manejar incrementos (like, dislike)
        inc_updates = {}
        if "like" in provided_data:
            inc_updates[f"{mission_field}.like"] = provided_data["like"]
        if "dislike" in provided_data:
            inc_updates[f"{mission_field}.dislike"] = provided_data["dislike"]
        
        if inc_updates:
            update_operations["$inc"] = inc_updates

        # Si no hay operaciones válidas
        if not update_operations:
            return EventResponse(
                id=person_id,
                message="No se proporcionaron parámetros válidos para actualizar",
                success=True
            )
        
        # Ejecutar actualización
        result = await db.assignments.update_one(
            {"person_id": person_id},
            update_operations
        )

        if result.modified_count > 0:
            return EventResponse(
                id=person_id,
                message="Parámetros de misión actualizados exitosamente",
                success=True
            )
        else:
            return EventResponse(
                id=person_id,
                message="No se realizaron cambios en los parámetros",
                success=True
            )
    
    except Exception as e:
        return EventResponse(
            id=person_id,
            message=f"Error actualizando los parámetros: {str(e)}",
            success=False
        )
    
async def missions_params_vote(
    user_id: str, 
    voter_id: str,
    update_data: ParamsUpdateVote, 
    db
):
    """
    Endpoint para actualizar parámetros específicos de una misión
    - Permite incrementar likes/dislikes solo si el coter no esta en la lista de voters
    - Comprueva si el numero de voters es igual al tamano del grupo y decide si la mission es aprobada o desaprobada
    """
    try:
        # Verificar si la asignación existe
        existing_assignment = await db.assignments.find_one({"person_id": user_id})
        
        if not existing_assignment:
            return EventResponse(
                id=user_id,
                message=f"No se encontró asignación para el person_id: {user_id}",
                success=False
            )
        
        # Verificar que la misión a actualizar existe y no es null
        mission_field = update_data.mission_type.value
        current_mission = existing_assignment.get(mission_field)
        

        if current_mission is None:
            return EventResponse(
                id=user_id,
                message=f"No se puede actualizar {mission_field} porque no existe",
                success=False
            )
        # comprobar si voto el usuario
        voters = current_mission["voters"]
        for voter in voters:
            if voter == voter_id:
                return EventResponse(
                id=user_id,
                message=f"El ususario ya voto ",
                success=False
            )

        votesNeeded = update_data.group_size-1
    
        if len(voters)>=votesNeeded:
            return EventResponse(
                id=user_id,
                message=f"La votacion esta llena",
                success=False
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
            archive_result = await archive_result_mission(user_id,current_mission,mission_field,status_result,db)
            if not archive_result:
                return EventResponse(
                    id=user_id,
                    message=f"No se pudo archivar la mision",
                    success=False
                )
            
            recompensa_result = await add_mission_recompensa(user_id,current_mission,mission_field,status_result,db)
            if not recompensa_result:
                return EventResponse(
                    id=user_id,
                    message=f"No se pudo registrar la recompensa",
                    success=False
                )
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
            return EventResponse(
                id=user_id,
                message="No se proporcionaron parámetros válidos para actualizar",
                success=True
            )
        
        # Ejecutar actualización
        result = await db.assignments.update_one(
            {"person_id": user_id},
            update_operations
        )

        if result.modified_count > 0:
            return EventResponse(
                id=user_id,
                message="Parámetros de misión actualizados exitosamente",
                success=True
            )
        else:
            return EventResponse(
                id=user_id,
                message="No se realizaron cambios en los parámetros",
                success=True
            )
    
    except Exception as e:
        return EventResponse(
            id=user_id,
            message=f"Error actualizando los parámetros: {str(e)}",
            success=False
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
        return True
    except Exception as e:
        print("error: ",{e})
        return False

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
        if result.matched_count > 0:
            return True
        else: return False
        
    except Exception as e:
        print(f"Error durante la actualizacion: {type(e).__name__}: {e}")
        return False
    

async def get_next_primary_mission(mission_id:str,db)->CreateMissionResponse:
    try:
        mission_id_int = int(mission_id)
        next_mission_id = str(mission_id_int+1)
        next_mission = await db.missions.find_one({"id": next_mission_id})
        if not next_mission:
            return CreateMissionResponse(
                message="no se encontro nueva mission primaria",
                mission_id="",
                mission_name="",
                success=False
            )
        return CreateMissionResponse(
                message="Siguiente mision principal encontrada",
                mission_id=next_mission["id"],
                mission_name=next_mission["nombre"],
                success=True
            )
    except ValueError:
        return CreateMissionResponse(
            message="Error: mission_id no es un número válido",
            mission_id="",
            mission_name="",
            success=False
        )
    except Exception as e:
        return CreateMissionResponse(
            message=f"Error inesperado: {str(e)}",
            mission_id="",
            mission_name="",
            success=False
        )