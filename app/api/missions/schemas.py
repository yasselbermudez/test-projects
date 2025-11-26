from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

class EventResponse(BaseModel):
    id: str
    message: str
    success: bool

class Nivel(BaseModel):
    numeroNivel: int
    descripcionNivel: str
    rangoXp: str
    imagen: str

class Extra(BaseModel):
    descripcion: str
    recompensa: str

class Logro(BaseModel):
    id: str 
    nombre: str
    descripcion: str
    pegatina: str
    misionAsociada: str
    idMision: str
    nivel: str

class MissionLogro(BaseModel):
    nombre: str
    descripcion: str
    pegatina: str

class Mission(BaseModel):
    id: str
    imagen: str
    nombre: str
    nivel: Nivel
    recompensa: str
    extra: Optional[Extra] = None
    descripcion: str
    logro: Optional[MissionLogro] = None
