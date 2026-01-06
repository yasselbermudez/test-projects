from datetime import datetime
import logging
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

MONGO_URL = settings.DATABASE_URL
DB_NAME = settings.DB_NAME

client = None

async def connect_to_mongo():
    global client
    # create client if it does not exist
    if client is None:
        client = AsyncIOMotorClient(MONGO_URL,serverSelectionTimeoutMS=5000, maxPoolSize=50)
    
        # serverSelectionTimeoutMS: server timeout
        # maxPoolSize: adjust according to load 
        
        try:
            # comprobar coneccion
            await client.admin.command('ping')
            logger.info("Connected to MongoDB")
        except Exception:
            client.close()
            client = None
            logger.exception("Could not connect to MongoDB on startup")
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

# MongoDB stores dates as BSON Date objects, not as Python objects.
def prepare_for_mongo(data):
    # If it's a dictionary, process each field
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Case 1: If it's a datetime object → convert to ISO string
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            # Case 2: If it's another dictionary → recursion
            elif isinstance(value, dict):
                result[key] = prepare_for_mongo(value)
            # Case 3: If it's a list → process each element
            elif isinstance(value, list):
                result[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
            # Case 4: Other types → direct copy
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

async def setup_ttl_indexes():
    "Configure the necessary TTL indexes in the database."
    db = get_database()
    if db is None:
        raise Exception("Database not initialized")
    
    await setup_refresh_token_indexes(db)
    logger.info("Índices TTL configurados")


async def setup_refresh_token_indexes(db):
    """Configure specific TTL indexes for refresh tokens"""
    try:
        await db.refresh_tokens.create_index(
            [("delete_at", 1)],  # Field and direction
            expireAfterSeconds=0,  # 0 = delete immediately upon exceeding the date
            name="auto_delete_refresh_tokens"
        )
    except Exception as e:
        logger.error(f"Error creating TTL index for refresh_tokens: {str(e)}")