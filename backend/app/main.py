import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import (
    cliente_routes,
    reserva_routes,
    quarto_routes,
    auth_routes,
    pagamento_routes,
    pontos_routes,
    real_points_routes,
    public_routes,
    voucher_routes,
    cielo_routes,
    cielo_test_routes,
    funcionario_routes,
    dashboard_routes,
    notificacao_routes,
    antifraude_routes,
    auditoria_routes,
    checkin_routes,
    pagamento_manual_routes,
    premios_routes,
    tarifas_routes,
    validacao_resgate_routes,
    consumo_routes,
    cancelamento_routes,
    operacional_routes,
    state_machine_routes,
    overbooking_routes,
    comprovante_routes,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    redirect_slashes=True  # Permite URLs com ou sem barra final
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        body_bytes = await request.body()
        body_preview = body_bytes[:4000].decode("utf-8", errors="replace")
    except Exception:
        body_preview = "<unavailable>"

    print("[422] RequestValidationError")
    print(f"[422] path={request.url.path}")
    print(f"[422] method={request.method}")
    print(f"[422] headers.content-type={request.headers.get('content-type')}")
    print(f"[422] errors={exc.errors()}")
    print(f"[422] body_preview={body_preview}")

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

app.mount("/media", StaticFiles(directory="media"), name="media")

# CORS Middleware - Configuração para suportar cookies e credenciais com ngrok
import os
# from app.middleware.ngrok_cors import DynamicCORSMiddleware

# Security Headers Middleware
from app.middlewares.security_headers import add_security_headers

# Obter origens CORS básicas do ambiente
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8080")
base_origins = [origin.strip() for origin in cors_origins_str.split(",")]

# Browsers bloqueiam cookies quando allow_credentials=True e Access-Control-Allow-Origin='*'.
# Então, se houver lista explícita de origens, usamos ela; se for '*', desativamos credenciais.
explicit_origins = [o for o in base_origins if o and o != "*"]
allow_credentials = True if explicit_origins else False
allow_origins = explicit_origins if explicit_origins else ["*"]

print(f"[CORS] Origens base: {base_origins}")
print(f"[CORS] Usando CORS padrão (debug)")

# Temporariamente usar CORS padrão para evitar o erro
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usar middleware personalizado que suporta ngrok dinamicamente
# app.add_middleware(DynamicCORSMiddleware, base_origins=base_origins)

# Security Headers Middleware
app.middleware("http")(add_security_headers)

# Include API Routes
app.include_router(cliente_routes.router, prefix="/api/v1")
app.include_router(reserva_routes.router, prefix="/api/v1")
app.include_router(quarto_routes.router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(pagamento_routes.router, prefix="/api/v1")
app.include_router(pontos_routes.router, prefix="/api/v1")
app.include_router(real_points_routes.router, prefix="/api/v1")
app.include_router(public_routes.router, prefix="/api/v1")
app.include_router(voucher_routes.router, prefix="/api/v1")
app.include_router(cielo_routes.router, prefix="/api/v1")
app.include_router(funcionario_routes.router, prefix="/api/v1")
app.include_router(dashboard_routes.router, prefix="/api/v1")
app.include_router(notificacao_routes.router, prefix="/api/v1")
app.include_router(antifraude_routes.router, prefix="/api/v1")
app.include_router(checkin_routes.router, prefix="/api/v1")
app.include_router(pagamento_manual_routes.router, prefix="/api/v1")
app.include_router(premios_routes.router, prefix="/api/v1")
app.include_router(validacao_resgate_routes.router, prefix="/api/v1")
app.include_router(comprovante_routes.router, prefix="/api/v1")
app.include_router(tarifas_routes.router, prefix="/api/v1")
app.include_router(cielo_test_routes.router, prefix="/api/v1")
app.include_router(auditoria_routes.router, prefix="/api/v1")
# app.include_router(consumo_routes.router, prefix="/api/v1")
# app.include_router(cancelamento_routes.router, prefix="/api/v1")
# app.include_router(operacional_routes.router, prefix="/api/v1")
# app.include_router(state_machine_routes.router, prefix="/api/v1")
# app.include_router(overbooking_routes.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    os.makedirs("media/avatars", exist_ok=True)
    await init_db()
    # Inicializar cache Redis
    from app.core.cache import cache
    await cache.connect()

@app.get("/")
async def root():
    return {
        "message": "Hotel Cabo Frio API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint works"}

@app.get("/api/v1/info")
async def api_info():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "clientes": "/api/v1/clientes",
            "reservas": "/api/v1/reservas",
            "quartos": "/api/v1/quartos",
            "funcionarios": "/api/v1/funcionarios",
            "auth": "/api/v1/auth/login",
            "pagamentos": "/api/v1/pagamentos",
            "pontos": "/api/v1/pontos",
            "antifraude": "/api/v1/antifraude",
            "dashboard": "/api/v1/dashboard/stats"
        }
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
