import uuid
from pydantic import BaseModel, Field
from typing import Dict, Optional

class InitProfile(BaseModel):
    email: str

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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    user_id: str
    edad: str
    apodo: str  # updateable
    titulo: str # te lo asigna la pagina
    peso_corporal: str # updateable
    altura: str 
    aura: str = "0" # te lo asigna la pagina
    deuda: Deuda # te lo asigna la pagina
    pesos: Pesos # updateable
    mujeres: str # updateable
    frase: str # updateable
    objetivo: str # updateable
    img: str

class ProfileUpdate(BaseModel):
    apodo: Optional[str] = None
    peso_corporal: Optional[str] = None
    pesos: Optional[Pesos] = None
    mujeres: Optional[str] = None
    frase: Optional[str] = None
    objetivo: Optional[str] = None    

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