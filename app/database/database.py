from datetime import datetime
import logging
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = settings.DATABASE_URL
DB_NAME = settings.DB_NAME

client = None

async def connect_to_mongo():
    global client
    # crear cliente si no existe 
    if client is None:
        client = AsyncIOMotorClient(MONGO_URL,serverSelectionTimeoutMS=5000, maxPoolSize=50)
        # serverSelectionTimeoutMS: tiempo de espera por el servidor 
        # maxPoolSize: ajustar segun carga 
    
        try:
            # comprobar coneccion
            await client.admin.command('ping')
            logging.info("Connected to MongoDB")
        except Exception:
            client.close()
            client = None
            logging.exception("Could not connect to MongoDB on startup")
            raise

    return client[DB_NAME]

async def close_mongo_connection():
    """Close the global Motor client."""
    global client
    if client is not None:
        client.close()
        client = None


def get_database():
    """Synchronous helper to get the DB from the running client."""
    if client is None:
        raise RuntimeError("Mongo client not initialized. Call connect_to_mongo() first.")
    return client[DB_NAME]

# MongoDB almacena fechas como objetos Date de BSON, no como objetos Python
def prepare_for_mongo(data):
    # Si es un diccionario, procesa cada campo
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Caso 1: Si es datetime → convierte a string ISO
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            # Caso 2: Si es otro diccionario → recursión
            elif isinstance(value, dict):
                result[key] = prepare_for_mongo(value)
            # Caso 3: Si es una lista → procesa cada elemento
            elif isinstance(value, list):
                result[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
            # Caso 4: Otros tipos → copia directa
            else:
                result[key] = value
        return result
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        result = {}
        for key, value in item.items():
            if key.endswith('_at') and isinstance(value, str):
                try:
                    result[key] = datetime.fromisoformat(value)
                except Exception:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = parse_from_mongo(value)
            elif isinstance(value, list):
                result[key] = [parse_from_mongo(v) if isinstance(v, dict) else v for v in value]
            else:
                result[key] = value
        return result
    return item