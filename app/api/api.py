from fastapi import APIRouter
from .products.routes import router as products_router

api_router = APIRouter()

# Public routes (no authentication required)
api_router.include_router(products_router.router, prefix="/products", tags=["Products"])
