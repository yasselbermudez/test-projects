from datetime import datetime
import uuid
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional

# Misiones secundarias
class ResultMission(BaseModel): 
    descriptionResult: Optional[str]
    voteDescription: int
    evaluation: bool

class SecondaryMission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    nombre: str
    descripcion: str
    recompensa: str
    is_active: bool = True
    created: datetime = Field(default_factory=datetime.now)

class EventResponse(BaseModel):
    message: str
    success: bool
    mission_id: str
    mission_name: str

class MissionApi(BaseModel):
    nombre:str
    descripcion:str
    recompensa:str