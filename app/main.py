import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.api import api_router
from app.core.config import settings
from app.database.database import close_mongo_connection, connect_to_mongo, setup_ttl_indexes
from starlette.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Show in console
        logging.FileHandler('app.log')  # Save to file
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await connect_to_mongo()
    await setup_ttl_indexes()
    yield
    # Shutdown logic
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for an online participation game.",
    docs_url="/docs",
    contact={
        "name": "Yassel",
        "email": "yasselbermudez8@gmail.com"
    },
    lifespan=lifespan
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="localhost",
        port=8000, 
        reload=True
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,                      # Necessary if use cookies
    allow_methods=["*"],                         # Allow OPTIONS, GET, POST, PUT, DELETE...
    allow_headers=["*"],                         # Allow Content-Type, Authorization, etc.
)

app.include_router(api_router,prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message":"Iron Brothers API is runing"}



