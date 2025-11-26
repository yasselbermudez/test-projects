from .schemas import Logro, Mission, EventResponse
import json
from app.database.database import prepare_for_mongo

# Importar desde el archivo init_missions.json
with open('./init_missions.json', 'r', encoding='utf-8') as f:
    missions = json.load(f)

with open('./init_logros.json', 'r', encoding='utf-8') as f:
    logros = json.load(f)

async def initialize_missions(db):
    # Obtener las misiones desde la variable cargada
    try:
        for mission in missions:
            mission_obj = Mission(**mission)
            mission_doc = prepare_for_mongo(mission_obj.dict())
            await db.missions.insert_one(mission_doc)

    except Exception as e:
        print(f"Error durante la inserción: {type(e).__name__}: {e}")

    return {"message": f"Initialized {len(missions)} missions."}

async def initialize_logros(db):
    # Obtener los logros desde la variable cargada
    try:
        for logro in logros:
            logro_obj = Logro(**logro)
            logro_doc = prepare_for_mongo(logro_obj.dict())
            await db.logros.insert_one(logro_doc)

    except Exception as e:
        print(f"Error durante la inserción: {type(e).__name__}: {e}")

    return {"message": f"Initialized {len(logros)} logros."}