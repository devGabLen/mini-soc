import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import alerts, incidents, profiles

logger = logging.getLogger("mini_soc")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="mini-soc-backend", version="0.1.0")

# CORS abierto: esto es un backend de desarrollo local (localhost:8080) al que
# le pega un dashboard corriendo en el navegador. No hay cookies de sesión
# involucradas (la auth es un Bearer token explícito), así que un origen
# abierto es razonable aquí. Para producción, restringir a los dominios reales.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(incidents.router)
app.include_router(alerts.router)


@app.get("/actuator/health")
def health() -> dict:
    return {"status": "UP"}


def _error_body(status: int, error: str, message: str, details: list | None = None) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error": error,
        "message": message,
        "details": details or [],
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(
        status_code=400,
        content=_error_body(400, "Bad Request", "Los datos enviados no son válidos.", details),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Nunca se devuelve el mensaje crudo de la excepción ni un stack trace al
    # cliente: solo un refId de correlación. El detalle real va al log interno.
    ref_id = str(uuid.uuid4())
    logger.exception("Error interno no controlado [ref=%s]", ref_id)
    return JSONResponse(
        status_code=500,
        content=_error_body(
            500, "Internal Server Error", f"Ocurrió un error inesperado. Ref: {ref_id}"
        ),
    )
