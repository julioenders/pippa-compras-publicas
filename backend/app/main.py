import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_engine
from app.routers import health, contratacoes, gestor_publico, sebrae_nacional, sebrae_uf, mpe, admin

logger = logging.getLogger(__name__)

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    logger.info("Database engine initialized")

    try:
        from app.collectors.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
    except Exception:
        logger.warning("Scheduler not started (collectors may not be configured yet)")

    yield

    try:
        from app.collectors.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="PIPPA Compras Públicas",
    description="Inteligência em Compras Governamentais para MPEs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(contratacoes.router, prefix="/api/v1/contratacoes", tags=["Contratações"])
app.include_router(gestor_publico.router, prefix="/api/v1/gestor-publico", tags=["Gestor Público"])
app.include_router(sebrae_nacional.router, prefix="/api/v1/sebrae-nacional", tags=["SEBRAE Nacional"])
app.include_router(sebrae_uf.router, prefix="/api/v1/sebrae-uf", tags=["SEBRAE UF"])
app.include_router(mpe.router, prefix="/api/v1/mpe", tags=["MPE"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
