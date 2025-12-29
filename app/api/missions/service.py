from .schemas import Logro, Mission
from fastapi import HTTPException,status
import json
from app.database.database import prepare_for_mongo

import logging
logger = logging.getLogger(__name__)

# Importar desde el archivo init_missions.json
with open('./init_missions.json', 'r', encoding='utf-8') as f:
    missions = json.load(f)

with open('./init_logros.json', 'r', encoding='utf-8') as f:
    logros = json.load(f)

async def initialize_missions(db):
    
    try:
        for mission in missions:
            mission_obj = Mission(**mission)
            mission_doc = prepare_for_mongo(mission_obj.dict())
            await db.missions.insert_one(mission_doc)

    except Exception as e:
        logger.error(f"Error initializing missions: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error initializing missions")
    return len(missions)

async def initialize_logros(db):
   
    try:
        for logro in logros:
            logro_obj = Logro(**logro)
            logro_doc = prepare_for_mongo(logro_obj.dict())
            await db.logros.insert_one(logro_doc)

    except Exception as e:
        logger.error(f"Error initializing logros: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error initializing logros")
    return len(logros)