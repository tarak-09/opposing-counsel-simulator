from fastapi import APIRouter

from .demo import router as demo_router
from .documents import router as documents_router
from .health import router as health_router
from .personas import router as personas_router
from .runs import router as runs_router


api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(demo_router, prefix="/demo", tags=["demo"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(personas_router, prefix="/personas", tags=["personas"])
api_router.include_router(runs_router, prefix="/runs", tags=["runs"])
