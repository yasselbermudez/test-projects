from fastapi import APIRouter
from app.api.products.routes import router as products_routes
from app.api.auth.routes import router as auth_routes

api_router = APIRouter()

# Public routes (no authentication required)
api_router.include_router(products_routes, prefix="/products", tags=["Products"])
api_router.include_router(auth_routes, prefix="/auth", tags=["Authorization"])
