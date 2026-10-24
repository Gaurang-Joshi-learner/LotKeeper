"""Application factory."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  (register tables on Base.metadata)
from app.api import account, admin, auth, orders, vehicles
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.seed import seed
from app.services.errors import DomainError
from app.services.inventory_service import InventoryService

log = logging.getLogger("lotkeeper")


def _sweep_once() -> int:
    with SessionLocal() as db:
        return InventoryService(db).expire_due_holds()


async def _sweeper(interval: int) -> None:
    """Background loop that frees units whose holds timed out, so stock reappears without a user request."""
    while True:
        await asyncio.sleep(interval)
        try:
            freed = await run_in_threadpool(_sweep_once)
            if freed:
                log.info("released %s expired hold(s)", freed)
        except Exception:  # keep the loop alive
            log.exception("hold sweeper failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    Base.metadata.create_all(engine)
    if settings.seed_on_startup:
        with SessionLocal() as db:
            seed(db)
    task = asyncio.create_task(_sweeper(settings.hold_sweep_seconds))
    try:
        yield
    finally:
        task.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Lotkeeper API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)

    @app.get("/api/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    for module in (auth, vehicles, account, orders, admin):
        app.include_router(module.router)
    return app


app = create_app()
