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
logger = logging.getLogger("assignments.service")

with open('./init_missions.json', 'r', encoding='utf-8') as f:
    missions = json.load(f)


async def get_assignments(person_id: str, db) -> Assignments:
    
    try:
        logger.info(f"Get assignments for user: {person_id}.")

        assignments = await db.assignments.find_one({"person_id":person_id})
        if not assignments:
            logger.error(f"No assignments were found for user: {person_id}."),
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"No assignments were found for user: {person_id}."
                )
        return Assignments(**assignments)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assignments: {str(e)}"),
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting assignments: {str(e)}"
        )


async def create_assignments(
    person_id: str,
    user_name: str,
    db,
) -> dict:
    try:
        logger.info(f"Creating assignments for user {person_id}.")

        mission_data = Mission(
            mission_id="1",
            mission_name=missions[0]["nombre"],  # Access as a dictionary
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
            logger.error(f"Error inserting assignments for user:{person_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inserting assignments for user:{person_id}"
            )
        
        logger.info(f"Assignments created for user: {person_id}")
        return {"assignment_id": str(result.inserted_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assignments: {str(e)}"
        )

# eliminar sustituir o agregar una mision a la asignacion
async def update_assignments_missions(
    user_id: str, 
    type:MissionType,
    db
)->Assignments:
    try:
        logger.info(f"Updating assignments mission for user: {user_id}.")

        existing_assignment = await db.assignments.find_one({"person_id": user_id})
        
        if not existing_assignment:
            logger.error(f"No assignment was found for the user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No assignment was found for the user: {user_id}",
            )

        update_fields = {}
        
        if type==MissionType.SECONDARY:
            new_mission = await create_secondary_mission(user_id,db)
            logger.info(f"New secondary mission created: {new_mission}")
        elif type==MissionType.MAIN:
            mission_id = existing_assignment[type]["mission_id"]
            new_mission = await get_next_primary_mission(mission_id,db)
            
        
        mission_obj = Mission(
            mission_name=new_mission.nombre,
            mission_id=new_mission.id
        )   
        logger.info("New mission validated")
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
            logger.info("Mission successfully updated in the assignment.")
        else:
            updated_assignment = existing_assignment
            logger.info("No changes were made to the assignment's missions.")
        return Assignments(**updated_assignment)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating the assignment missions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error updating the assignment missions: {str(e)}")



async def get_assignments_missions(person_id: str, db) -> AssignmentsMissionsResponse:
    try:
        logger.info(f"Getting assignments missions for user: {person_id}.")
        assignments = await db.assignments.find_one({"person_id": person_id})

        if not assignments:
           logger.error(f"No assignment was found for the user: {person_id}")
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND, 
               detail=f"No assignment was found for the user: {person_id}."
               )
        
        assignments_obj = Assignments(**assignments)
        
        # Search for secondary_mission if it exists.
        secondary_mission = None
        if (assignments_obj.secondary_mission and 
            assignments_obj.secondary_mission.mission_id):
            
            secondary_mission = await db.secondary.find_one({
                "id": assignments_obj.secondary_mission.mission_id
            })
            if not secondary_mission:
                logger.error(f"Secondary mission with id {assignments_obj.secondary_mission.mission_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Secondary mission with id {assignments_obj.secondary_mission.mission_id} not found."
                )
        
        # Search for primary_mission if it exists.
        mission = None
        if (assignments_obj.mission and 
            assignments_obj.mission.mission_id):
            
            mission = await db.missions.find_one({
                "id": assignments_obj.mission.mission_id
            })
            if not mission:
                logger.error(f"Primary mission with id {assignments_obj.mission.mission_id} not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Primary mission with id {assignments_obj.mission.mission_id} not found."
                )

        response =  AssignmentsMissionsResponse(
            mission=mission,
            secondary_mission=secondary_mission
        )

        return response
    except HTTPException:    
        raise
    except Exception as e:
        logger.error(f"Error retrieving missions from the assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error retrieving missions from the assignments: {str(e)}"
            )


async def update_missions_params(
    person_id: str, 
    update_data: ParamsUpdate, 
    db
)->Assignments:
    """
    Endpoint for updating specific parameters of a mission.
    - Only updates existing missions (not null).
    - Allows changing status, result, likes, and dislikes.
    """
    try:
        logger.info(f"update mission parameters for user: {person_id}")
        existing_assignment = await db.assignments.find_one({"person_id": person_id})
        
        if not existing_assignment:
            logger.error(f"No assignment was found for the user: {person_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"No assignment was found for the user: {person_id}"
                )

        # Verify that the mission to be updated exists and is not null.
        mission_field = update_data.mission_type.value
        current_mission = existing_assignment.get(mission_field)
        
        if current_mission is None:
            logger.error(f"The {mission_field} cannot be updated because it does not exist.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"The {mission_field} cannot be updated because it does not exist.",
            )

        # Prepare update operations
        update_operations = {}
        provided_data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        # Handle like and dislike fields as regular status and result fields
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

        # If there are no valid operations
        if not update_operations:
            logger.error("No valid parameters were provided for the update.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No valid parameters were provided for the update.",
            )
        
        result = await db.assignments.update_one(
            {"person_id": person_id},
            update_operations
        )

        if result.modified_count > 0:
            updated_assignment = await db.assignments.find_one({"person_id": person_id})
            logger.info("No changes were made to the assignment parameters")
        else:
            updated_assignment = existing_assignment
            logger.info("Assignment parameters updated successfully")
        return updated_assignment
        
    except Exception as e:
        logger.error(f"Error updating the assignment parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error updating the assignment parameters: {str(e)}"
            )
    
async def update_missions_params_vote(
    user_id: str, 
    voter_id: str,
    update_data: ParamsUpdateVote, 
    db
)->Assignments:
    """
    Endpoint to update specific parameters of a mission.
    - Allows increasing likes/dislikes only if the voter is not already in the list of voters.
    - Checks if the number of voters is equal to the group size and decides whether the mission is approved or disapproved.
    """
    try:
        logger.info(f"Updating mission vote parameters for user: {user_id}")
        existing_assignment = await db.assignments.find_one({"person_id": user_id})
        
        if not existing_assignment:
            logger.error(f"No assignment was found for the user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No assignment was found for the user: {user_id}",
            )
        
        # Verify that the mission to be updated exists and is not null.
        mission_field = update_data.mission_type.value
        current_mission = existing_assignment.get(mission_field)
        
        if current_mission is None:
            logger.error(f"Cannot update {mission_field} because it does not exist.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Cannot update {mission_field} because it does not exist.",
            )
        
        
        # Check if the user voted
        voters = current_mission["voters"]
        for voter in voters:
            if voter == voter_id:
                logger.error(f"The user: {voter_id} has already voted")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"The user: {voter_id} has already voted",
                )

        votesNeeded = update_data.group_size-1
    
        if len(voters)>=votesNeeded:
            logger.error("The voting is full")
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="The voting is full",
            )
        
        # prepare the base of the update operations
        set_updates = {}
        # Add new voter
        newListUsers = voters + [voter_id]
        set_updates[f"{mission_field}.voters"] = newListUsers
        # Handle increments like or dislike)
        like_count=current_mission["like"]
        dislike_count=current_mission["dislike"]
        
        if  update_data.like:
            like_count+=1
            set_updates[f"{mission_field}.like"] = like_count
        else:
            set_updates[f"{mission_field}.dislike"] = dislike_count
            dislike_count+=1

        
        # We check if it's the last vote
        if len(voters)+1>=votesNeeded:

            # Final result of the mission
            status_result = ""
            if like_count>=dislike_count:
                status_result = MissionStatus.COMPLETED
            else: status_result = MissionStatus.FAILED

            logger.info(f"Mission status set to: {status_result}")
            set_updates[f"{mission_field}.status"] = status_result
    
            # We process the result of the mission 
            await archive_result_mission(user_id,current_mission,mission_field,status_result,db)
            
            # We process the mission reward
            await add_mission_recompensa(user_id,current_mission,mission_field,status_result,db)

        update_operations = {}
        if set_updates:
            update_operations["$set"] = set_updates

        # If there are no valid operations
        if not update_operations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No valid parameters were provided for update",
            )
        
        result = await db.assignments.update_one(
            {"person_id": user_id},
            update_operations
        )
        
        if result.modified_count > 0:
            updated_assignment = await db.assignments.find_one({"person_id": user_id})
            logger.info("Voting parameters updated successfully.")
        else:
            updated_assignment = existing_assignment
            logger.info("No changes were made to the voting parameters.")
        return Assignments(**updated_assignment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing the vote: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing the vote: {str(e)}",
        )
    

async def archive_result_mission(user_id:str,current_mission:dict,mission_field:MissionType,status_result:str,db):
    """
    We are preparing the mission to be archived as a historical event.
    """
    try:
        logger.info(f"Archiving mission result for user: {user_id}")
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
        logger.info("Mission result archived successfully")   
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving mission result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error archiving mission result: {str(e)}",
        )

async def add_mission_recompensa(user_id:str,current_mission:dict,mission_field:str,status_result:MissionStatus,db):
    """
    # We process the reward based on the mission outcome.
    """
    try:
        logger.info(f"Processing mission reward for user: {user_id}")
        current_mission_obj:Mission = Mission(**current_mission)
        mission_id=current_mission_obj.mission_id
        
        if mission_field==MissionType.MAIN:
            mission_details = await db.missions.find_one({"id":mission_id})
        else: 
            mission_details = await db.secondary.find_one({"id":mission_id})
        
        if not mission_details:
            logger.error(f"Mission details not found for mission_id: {mission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission details not found for mission_id: {mission_id}",
            )
        
        recompensa = mission_details["recompensa"]
        recompensa_int = int(recompensa)

        if status_result == MissionStatus.FAILED:
            recompensa_int = - recompensa_int
 
        user_profile_data = await db.profiles.find_one({"user_id":user_id})
        
        if not user_profile_data:
            logger.error(f"Profile not found for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found for user_id: {user_id}",
            )
        
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
            logger.error(f"Failed to register reward for user_id:{user_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Failed to register reward for user_id:{user_id}",
            )
        logger.info("Mission reward processed successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing the reward: {e}")
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing the reward",
            )
    

async def get_next_primary_mission(mission_id:str,db)->PrimaryMission:
    try:
        logger.info(f"Getting next primary mission")
        mission_id_int = int(mission_id)
        next_mission_id = str(mission_id_int+1)
        next_mission = await db.missions.find_one({"id": next_mission_id})
        if not next_mission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The following main mission was not found.",
            )
        logger.info(f"Next primary mission found")
        return PrimaryMission(**next_mission)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next main mission.: {str(e)}")
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting next main mission.: {str(e)}",
            )