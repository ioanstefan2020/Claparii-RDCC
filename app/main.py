import importlib
import os
import pkgutil
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.schemas.common import AppError

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"

app = FastAPI(title="Accesibilitate Workplace API")


# Auto-discover routers from app/routers/
def register_routers():
    import app.routers as routers_pkg

    package_path = routers_pkg.__path__
    for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
        if not is_pkg:
            full_module_name = f"app.routers.{module_name}"
            mod = importlib.import_module(full_module_name)
            router = getattr(mod, "router", None)
            if router is not None:
                app.include_router(router)


# Register discovered routers
try:
    register_routers()
except Exception as e:
    # Safe handling during initial bootstrap
    pass


# GET /api/health
@app.get("/api/health")
async def health_check():
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER)
    return {"ok": True, "provider": provider}


# Global Exception Handlers returning error envelope:
# {"ok": false, "error": {"code": "...", "message_ro": "..."}}
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {"code": exc.code, "message_ro": exc.message_ro},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": {
                "code": "bad_request",
                "message_ro": "Datele trimise sunt invalide sau lipsesc câmpuri obligatorii.",
            },
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: "bad_request",
        404: "not_found",
        422: "bad_request",
        500: "internal",
        502: "bad_llm_output",
        503: "llm_unavailable",
    }
    code = code_map.get(exc.status_code, "error")
    msg = (
        exc.detail
        if isinstance(exc.detail, str)
        else "A apărut o eroare la procesarea cererii."
    )
    if exc.status_code == 404:
        msg = "Resursa cerută nu a fost găsită."

    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": {"code": code, "message_ro": msg}},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": {
                "code": "internal",
                "message_ro": "A apărut o eroare internă. Te rugăm să încerci din nou.",
            },
        },
    )


# Serve web/ at / if the directory exists
if WEB_DIR.exists() and WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
