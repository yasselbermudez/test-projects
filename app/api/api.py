from fastapi import APIRouter
from app.api.profiles.routes import router as profiles_routes
from app.api.auth.routes import router as auth_routes
from app.api.users.routes import router as users_routes
from app.api.missions.routes import router as missions_routes
from app.api.history.routes import router as history_routes
from app.api.second_missions.routes import router as secondary_routes
from app.api.assignments.routes import router as assignments_routes
from app.api.group.routes import router as group_routes

api_router = APIRouter()

# Public routes (no authentication required)
api_router.include_router(profiles_routes, prefix="/profiles", tags=["Profiles"])
api_router.include_router(auth_routes, prefix="/auth", tags=["Authorization"])
api_router.include_router(users_routes, prefix="/users", tags=["Users"])
api_router.include_router(missions_routes, prefix="/missions", tags=["Missions"])
api_router.include_router(history_routes, prefix="/history", tags=["History"])
api_router.include_router(secondary_routes, prefix="/secondary", tags=["Secondary Missions"])
api_router.include_router(assignments_routes, prefix="/assignments", tags=["Assignments"])
api_router.include_router(group_routes, prefix="/groups", tags=["Group"])
