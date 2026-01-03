from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.api import api_router
from app.core.config import settings
from app.database.database import close_mongo_connection, connect_to_mongo, setup_ttl_indexes
from starlette.middleware.cors import CORSMiddleware

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
    description="API para un juego de participacion en línea.",
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
    allow_origins=settings.BACKEND_CORS_ORIGINS, # OR use ["*"] solo en desarrollo
    allow_credentials=True,                      # necesario si vas a usar cookies
    allow_methods=["*"],                         # permite OPTIONS, GET, POST, PUT, DELETE...
    allow_headers=["*"],                         # permite Content-Type, Authorization, etc.
)

app.include_router(api_router,prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message":"Iron Brothers API is runing"}



