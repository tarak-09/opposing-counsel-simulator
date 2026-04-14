from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.personas import sync_builtin_personas


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    with SessionLocal() as session:
        sync_builtin_personas(session)
    yield


app = FastAPI(
    title="Opposing Counsel Simulator API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
