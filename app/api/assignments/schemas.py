from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from ..missions.schemas import Mission as MissionResponse
from ..second_missions.schemas import SecondaryMission as SecondaryMissionResponse

class EventResponse(BaseModel):
    id: str
    message: str
    success: bool

class MissionType(str, Enum):
    MAIN = "mission"
    SECONDARY = "secondary_mission"
    GROUP = "group_mission"

class MissionStatus(str, Enum):
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    FAILED = "failed"

class Mission(BaseModel):
    mission_name: str 
    mission_id: str
    status: MissionStatus = MissionStatus.ACTIVE
    creation_date: datetime = datetime.now()
    result: str = ""
    like: int = 0
    dislike: int = 0
    voters: list[str] = []    

class Assignments(BaseModel): 
    person_id: str
    person_name: str
    mission: Mission
    secondary_mission: Optional[Mission] = None
    group_mission: Optional[Mission] = None

#endpoint que devuelve los documentos de las misiones asignadas
class AssignmentsMissionsResponse(BaseModel): 
    mission: Optional[MissionResponse] = None
    secondary_mission: Optional[SecondaryMissionResponse] = None


# actualizacion de la mision
class MissionUpdate(BaseModel):
    mission_name: str 
    mission_id: str

class UpdateAssignments(BaseModel):
    mission: Optional[MissionUpdate] = None
    secondary_mission: Optional[MissionUpdate] = None
    group_mission: Optional[MissionUpdate] = None

# actualizaciones parciales de los parametros de las misiones de cada asignacion
class ParamsUpdate(BaseModel):
    mission_type: MissionType
    status: Optional[MissionStatus] = None
    result: Optional[str] = None
    like: Optional[int] = None
    dislike: Optional[int] = None

class ParamsUpdateVote(BaseModel):
    mission_type: MissionType
    like: bool
    group_size: int

class MissionParamsUpdate(BaseModel):
    mission: Optional[ParamsUpdate] = None
    secondary_mission: Optional[ParamsUpdate] = None
    group_mission: Optional[ParamsUpdate] = None