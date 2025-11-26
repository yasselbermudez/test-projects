from .schemas import Profile, Summary
import json
from app.database.database import prepare_for_mongo

# Importar desde el archivo init_data.json
with open('./init_profiles.json', 'r', encoding='utf-8') as f:
    profiles = json.load(f)

with open('./init_summary.json', 'r', encoding='utf-8') as f:
    summarys = json.load(f)

async def initialize_profile_data(user_id,email,db):
    # Obtener los ejercicios de ejemplo desde la variable cargada
    try:
        for profile in profiles:
            if profile["email"] == email:
                profile["user_id"] = user_id
                profile_obj = Profile(**profile)
                profile_doc = prepare_for_mongo(profile_obj.dict())
                result = await db.profiles.update_one(
                    {"user_id": profile_doc["user_id"]},    # Filtro
                    {"$set": profile_doc},                  # Datos a actualizar
                    upsert=True                             # Insertar si no existe
                )
                #if result.upserted_id: print("Documento insertado")
                #else: print("Documento actualizado")
                return {"message": f"Initialized profile for user with email: {email}"}

    except Exception as e:
        print(f"Error durante la inserción: {type(e).__name__}: {e}")

    return {"message": f"Not initialized profile for user with email: {email}"}

async def initialize_summary_data(user_id,email,db):
    # Obtener los ejercicios de ejemplo desde la variable cargada
    try:
        for summary in summarys:
            if summary["email"]==email:
                summary["user_id"] = user_id
                summary_obj = Summary(**summary)
                summary_doc = prepare_for_mongo(summary_obj.dict())
                result = await db.summary.update_one(
                    {"user_id": summary_doc["user_id"]},    # Filtro
                    {"$set": summary_doc},                  # Datos a actualizar
                    upsert=True                             # Insertar si no existe
                )
                #if result.upserted_id: print("Documento insertado")
                #else: print("Documento actualizado")
                return {"message": f"Initialized summary for user with email: {email}"}


    except Exception as e:
        print(f"Error insertando summary: {type(e).__name__}: {e}")

    return {"message": f"Not initialized summary for user with email: {email}"}
