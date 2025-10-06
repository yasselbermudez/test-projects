from fastapi import FastAPI
from app.api.api import api_router
from app.core.config import settings

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


