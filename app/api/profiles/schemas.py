import uuid
from pydantic import BaseModel, Field
from typing import Dict, Optional

class EventResponse(BaseModel):
    message: str
    success: bool

class Deuda(BaseModel):
    tipo: str
    cantidad: str

class Pesos(BaseModel):
    pressBanca: str
    sentadilla: str
    pesoMuerto: str
    prensa: str
    biceps: str

class Profile(BaseModel):
    name: str
    email: str
    user_id: str
    edad: str
    estatura: str 
    peso_corporal: str # updateable
    pesos: Pesos # updateable
    apodo: str = "" # updateable
    titulo: str = "" # te lo asigna la pagina
    aura: str = "0" # te lo asigna la pagina
    deuda: Optional[Deuda] = None # te lo asigna la pagina
    mujeres: str = "" # updateable
    frase: str = ""# updateable
    objetivo: str = "" # updateable
    img: str = ""

class ProfileUpdate(BaseModel):
    apodo: Optional[str] = None
    peso_corporal: Optional[str] = None
    pesos: Optional[Pesos] = None
    mujeres: Optional[str] = None
    frase: Optional[str] = None
    objetivo: Optional[str] = None    

class ProfileInit(BaseModel):
    edad: str
    peso_corporal: str
    estatura: str
    pesos: Pesos
    frase: Optional[str] = None
    apodo: Optional[str] = None
    objetivo: Optional[str] = None
    summary: Optional[str] = None


class Summary(BaseModel):
    user_id: str
    email:str
    identidad_basica: Dict[str, str] = Field(default_factory=dict)
    caracteristicas_fisicas: Dict[str, str] = Field(default_factory=dict)
    personalidad_psicologia: Dict[str, str] = Field(default_factory=dict)
    trayectoria_vital_situacion_actual: Dict[str, str] = Field(default_factory=dict)
    gustos_red_social_estilo_vida: Dict[str, str] = Field(default_factory=dict)
    perfil_sintetizado: str
   # fecha_creacion: datetime
   # ultima_actualizacion: datetime