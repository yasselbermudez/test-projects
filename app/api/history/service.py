from .schemas import Event,EventResponse
from app.database.database import prepare_for_mongo

async def create_event(event_data: Event, db) -> EventResponse:
    try:
        # Conversión directa 
        event_data_doc = prepare_for_mongo(event_data.dict())
        
        result = await db.history.insert_one(event_data_doc)
        
        # Retorna respuesta estructurada
        return EventResponse(
            id=str(result.inserted_id),
            message="Event created successfully",
            success=True
        )
        
    except Exception as e:
        # En producción, usa logging aquí
        print(f"Error creating event: {e}")
        return EventResponse(
            id="",
            message=f"Error creating event: {str(e)}",
            success=False
        )

"""
async def create_event(event_data:Event, db):
    event_data_dict = event_data.dict()
    #del event_data_dict["result"]
    event_data_object = Event(**event_data_dict)
    event_data_doc = prepare_for_mongo(event_data.dict())
    #event_data_doc["name"] = "nueva mision"
    result = await db.history.insert_one(event_data_doc)
    return result
"""