"""
ENDPOINT CRÍTICO - Diagnóstico Runtime DATABASE_URL
Prova definitiva de qual banco o Prisma Client está usando
"""
from fastapi import APIRouter
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
import os
import asyncio
from app.core.database import db

router = APIRouter(prefix="/runtime-debug", tags=["runtime-debug"])


@router.get("/database-connection-proof")
async def database_connection_proof():
    """
    PROVA DEFINITIVA: Qual DATABASE_URL o Prisma Client está usando em runtime.
    
    CRITÉRIO DE SUCESSO:
    - Se retornar host 'db.prisma.io' = CORRETO (Prisma Data Platform)
    - Se retornar host 'postgres' ou 'localhost' = PROBLEMA (banco local)
    """
    try:
        result = {
            "timestamp": now_utc().isoformat(),
            "status": "unknown",
            "environment_vars": {},
            "prisma_client_info": {},
            "connection_test": {},
            "critical_diagnosis": "PENDING"
        }
        
        # 1. VERIFICAR VARIÁVEIS DE AMBIENTE
        result["environment_vars"] = {
            "DATABASE_URL_from_os": os.getenv("DATABASE_URL", "NOT_SET"),
            "DATABASE_URL_masked": _mask_url(os.getenv("DATABASE_URL", "")),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT_SET"),
            "PWD": os.getenv("PWD", "NOT_SET")
        }
        
        # 2. VERIFICAR PRISMA CLIENT
        try:
            # Tentar conectar se não conectado
            if not db.is_connected():
                await db.connect()
            
            result["prisma_client_info"] = {
                "is_connected": db.is_connected(),
                "client_type": str(type(db)),
                "client_repr": repr(db)[:200]  # Limitar tamanho
            }
            
            # 3. TESTE DE CONEXÃO CRÍTICO
            if db.is_connected():
                # Executar query para identificar o host real
                try:
                    # Query para obter informações do servidor
                    raw_result = await db.query_raw("SELECT version(), current_database(), inet_server_addr() as server_ip")
                    
                    if raw_result:
                        server_info = raw_result[0] if raw_result else {}
                        result["connection_test"] = {
                            "database_version": server_info.get("version", "UNKNOWN"),
                            "current_database": server_info.get("current_database", "UNKNOWN"),
                            "server_ip": server_info.get("server_ip", "UNKNOWN"),
                            "query_success": True
                        }
                        
                        # DIAGNÓSTICO CRÍTICO
                        server_ip = server_info.get("server_ip", "")
                        if "prisma" in str(server_info.get("version", "")).lower() or server_ip.startswith("10."):
                            result["critical_diagnosis"] = "SUCCESS_PRISMA_REMOTE"
                            result["status"] = "CORRETO - Usando Prisma Data Platform"
                        else:
                            result["critical_diagnosis"] = "PROBLEM_LOCAL_DB"
                            result["status"] = "PROBLEMA - Usando banco local!"
                    
                except Exception as query_error:
                    result["connection_test"] = {
                        "query_success": False,
                        "query_error": str(query_error)
                    }
                    result["critical_diagnosis"] = "QUERY_FAILED"
                    result["status"] = "ERRO - Falha na query de diagnóstico"
            
            else:
                result["critical_diagnosis"] = "NOT_CONNECTED"
                result["status"] = "ERRO - Prisma Client não conectado"
                
        except Exception as prisma_error:
            result["prisma_client_info"] = {
                "error": str(prisma_error),
                "is_connected": False
            }
            result["critical_diagnosis"] = "PRISMA_ERROR"
            result["status"] = f"ERRO - Prisma Client: {str(prisma_error)}"
        
        # 4. CONTAGEM DE REGISTROS PARA COMPARAÇÃO
        try:
            if db.is_connected():
                counts = {}
                
                # Contar registros principais
                counts["reservas"] = await db.reserva.count()
                counts["clientes"] = await db.cliente.count()
                counts["quartos"] = await db.quarto.count()
                counts["funcionarios"] = await db.funcionario.count()
                
                result["record_counts"] = counts
                
                # Diagnóstico baseado nas contagens
                total_records = sum(counts.values())
                if total_records < 20:  # Poucos registros = provavelmente banco local/vazio
                    result["count_diagnosis"] = "SUSPICIOUS_LOW_COUNTS - Possível banco local"
                else:
                    result["count_diagnosis"] = "NORMAL_COUNTS - Provavelmente banco correto"
                    
        except Exception as count_error:
            result["record_counts"] = {"error": str(count_error)}
            result["count_diagnosis"] = "COUNT_ERROR"
        
        return result
        
    except Exception as e:
        return {
            "timestamp": now_utc().isoformat(),
            "status": "CRITICAL_ERROR",
            "error": str(e),
            "critical_diagnosis": "SYSTEM_ERROR"
        }


@router.get("/prisma-client-raw-info")
async def prisma_client_raw_info():
    """
    Informações brutas do Prisma Client para debug avançado
    """
    try:
        info = {
            "timestamp": now_utc().isoformat(),
            "prisma_client_attributes": {},
            "environment_dump": {},
            "working_directory": os.getcwd()
        }
        
        # Atributos do cliente Prisma
        try:
            client_attrs = {}
            for attr in dir(db):
                if not attr.startswith('_'):
                    try:
                        value = getattr(db, attr)
                        if not callable(value):
                            client_attrs[attr] = str(value)[:100]  # Limitar tamanho
                    except:
                        client_attrs[attr] = "ERROR_ACCESSING"
            
            info["prisma_client_attributes"] = client_attrs
        except Exception as e:
            info["prisma_client_attributes"] = {"error": str(e)}
        
        # Dump de variáveis de ambiente relevantes
        env_vars = {}
        for key, value in os.environ.items():
            if any(keyword in key.upper() for keyword in ["DATABASE", "PRISMA", "POSTGRES", "DB"]):
                env_vars[key] = _mask_url(value) if "URL" in key else value
        
        info["environment_dump"] = env_vars
        
        return info
        
    except Exception as e:
        return {
            "timestamp": now_utc().isoformat(),
            "error": str(e),
            "status": "ERROR"
        }


def _mask_url(url: str) -> str:
    """Mascarar credenciais da URL para log seguro"""
    if not url or len(url) < 10:
        return url
    
    try:
        if "@" in url:
            parts = url.split("@")
            if len(parts) >= 2:
                # Manter protocolo e host, mascarar credenciais
                protocol_and_creds = parts[0]
                host_and_path = "@".join(parts[1:])
                
                if "://" in protocol_and_creds:
                    protocol = protocol_and_creds.split("://")[0]
                    return f"{protocol}://****:****@{host_and_path}"
        
        return url[:20] + "..." if len(url) > 20 else url
    except:
        return "MASK_ERROR"
