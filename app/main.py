import importlib
import logging
import os
import pkgutil
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.llm import log_llm_startup, warm_up_llm
from app.schemas.common import AppError

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"

logger = logging.getLogger("primazi.api")
logging.basicConfig(level=logging.INFO, format="%(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await warm_up_llm()
    yield


app = FastAPI(
    title="PrimaZi API — Asistent Accesibil pentru Primul Loc de Muncă",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware (Task P1-15)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Metrics & Privacy-Safe Logging & Security Headers Middleware (Tasks N1.7 & P1-15)
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        status = response.status_code
        # Add latency header for UI & client diagnostics
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        # Security headers (Task P1-15)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        logger.info(f"[METRICS] {method} {path} -> {status} ({duration:.3f}s)")
        return response
    except Exception as exc:
        duration = time.perf_counter() - start_time
        logger.info(
            f"[METRICS] {method} {path} -> ERROR: {type(exc).__name__} ({duration:.3f}s)"
        )
        raise exc


# Auto-discover routers from app/routers/
def register_routers():
    import app.routers as routers_pkg

    package_path = routers_pkg.__path__
    for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
        if not is_pkg:
            full_module_name = f"app.routers.{module_name}"
            try:
                mod = importlib.import_module(full_module_name)
                router = getattr(mod, "router", None)
                if router is not None:
                    app.include_router(router)
            except Exception as e:
                logger.error(f"[ROUTER ERROR] Failed to load {full_module_name}: {e}")


# Register discovered routers and log startup status
try:
    register_routers()
    log_llm_startup()
except Exception as e:
    logger.error(f"[STARTUP ERROR] initialization failed: {e}")


# GET /api/health
@app.get("/api/health")
async def health_check():
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER)
    return {"ok": True, "provider": provider}


# Global Exception Handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {"code": exc.code, "message_ro": exc.message_ro},
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    code = "not_found" if exc.status_code == 404 else "bad_request"
    msg_ro = (
        "Pagina sau resursa nu a fost găsită."
        if exc.status_code == 404
        else str(exc.detail)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": {"code": code, "message_ro": msg_ro}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": {
                "code": "bad_request",
                "message_ro": "Datele trimise nu respectă formatul cerut.",
            },
        },
    )


# Mount static files at / (web directory)
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="static")
