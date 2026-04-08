from fastapi import APIRouter

from server.api.sources import router as sources_router
from server.api.tasks import router as tasks_router
from server.api.logs import router as logs_router
from server.api.stats import router as stats_router

api_router = APIRouter(prefix="/api")
api_router.include_router(sources_router)
api_router.include_router(tasks_router)
api_router.include_router(logs_router)
api_router.include_router(stats_router)
