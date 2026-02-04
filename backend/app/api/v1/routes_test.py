"""
Endpoint para testar todas as rotas e diagnosticar problemas
"""
from fastapi import APIRouter
from datetime import datetime
from app.utils.datetime_utils import now_utc

router = APIRouter(prefix="/routes-test", tags=["routes-test"])

@router.get("/list-all-routes")
async def list_all_routes():
    """Listar todas as rotas disponíveis para diagnóstico"""
    try:
        from fastapi import FastAPI
        from app.main import app
        
        routes_info = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes_info.append({
                    "path": route.path,
                    "methods": list(route.methods) if route.methods else [],
                    "name": getattr(route, 'name', 'unnamed')
                })
        
        return {
            "timestamp": now_utc().isoformat(),
            "total_routes": len(routes_info),
            "routes": routes_info
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": now_utc().isoformat()
        }

@router.get("/test-imports")
async def test_imports():
    """Testar se todos os módulos de rotas podem ser importados"""
    import_results = {}
    
    modules_to_test = [
        "app.api.v1.reserva_routes",
        "app.api.v1.pagamento_routes", 
        "app.api.v1.pontos_routes",
        "app.api.v1.cliente_routes",
        "app.api.v1.quarto_routes",
        "app.api.v1.funcionario_routes",
        "app.api.v1.dashboard_routes",
        "app.api.v1.cielo_routes",
        "app.api.v1.antifraude_routes",
        "app.api.v1.notificacao_routes"
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            import_results[module_name] = {"status": "success", "error": None}
        except Exception as e:
            import_results[module_name] = {"status": "error", "error": str(e)}
    
    return {
        "timestamp": now_utc().isoformat(),
        "import_results": import_results
    }

@router.get("/test-services")
async def test_services():
    """Testar se os serviços podem ser instanciados"""
    service_results = {}
    
    try:
        from app.core.database import get_db
        db = get_db()
        service_results["database"] = {"status": "success", "connected": db.is_connected()}
    except Exception as e:
        service_results["database"] = {"status": "error", "error": str(e)}
    
    # Testar serviços específicos
    services_to_test = [
        ("ReservaService", "app.services.reserva_service", "ReservaService"),
        ("PagamentoService", "app.services.pagamento_service", "PagamentoService"),
        ("PontosService", "app.services.pontos_service", "PontosService")
    ]
    
    for service_name, module_name, class_name in services_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            service_class = getattr(module, class_name)
            service_results[service_name] = {"status": "success", "class_found": True}
        except Exception as e:
            service_results[service_name] = {"status": "error", "error": str(e)}
    
    return {
        "timestamp": now_utc().isoformat(),
        "service_results": service_results
    }
