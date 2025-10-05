from fastapi import FastAPI
from app.api.api import api_router

app = FastAPI(
    title="Online Store API",
    version="1.0.0",
    description="API para una tienda en línea",
    docs_url="/docs",
    contact={
        "name": "Yassel",
        "email": "yasselbermudez8@gmail.com"
    },
    )

app.include_router(api_router,prefix="/api/v1")

# Check healty
@app.get("/")
def root():
    return {"message":"Online Store API is runing"}


