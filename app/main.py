from fastapi import FastAPI
from app.api.api import api_router
from app.core.config import settings
from app.database.database import close_mongo_connection, connect_to_mongo

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para una tienda en línea",
    docs_url="/docs",
    contact={
        "name": "Yassel",
        "email": "yasselbermudez8@gmail.com"
    },
    )

app.include_router(api_router,prefix=settings.API_V1_STR)

# Check healty
@app.get("/")
def root():
    return {"message":"Online Store API is runing"}

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()


