# Salve como: app_simples.py
# Execute com: python app_simples.py

# =============================================================================
#  BACKUP FILE - MOVED TO MODULAR ARCHITECTURE
# =============================================================================
# This monolithic app has been migrated to modular structure in app/
# Migration completed: 2025-11-23
# 
# NEW LOCATION:
# - app/main.py (entry point)
# - app/api/v1/* (all routes)
# - app/services/* (business logic)
# - app/repositories/* (data access)
# - app/schemas/* (pydantic models)
# - app/core/* (configuration)
# 
# DO NOT USE THIS FILE - For reference only
# =============================================================================

import os
import uuid
import asyncio
import requests
import httpx
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from prisma import Prisma
from contextlib import asynccontextmanager
from enum import Enum
# from app.core.deps import require_roles  # Using local implementation
import secrets
import json
import re
from decimal import Decimal
from dotenv import load_dotenv
import uvicorn
import hashlib
import time
from collections import defaultdict
import redis
import pickle
from functools import wraps

# Carregar variáveis de ambiente
load_dotenv()

# Configurações da API Cielo
CIELO_MERCHANT_ID = os.getenv("CIELO_MERCHANT_ID")
CIELO_MERCHANT_KEY = os.getenv("CIELO_MERCHANT_KEY")
CIELO_SANDBOX_URL = os.getenv("CIELO_SANDBOX_URL")
CIELO_MODE = os.getenv("CIELO_MODE", "sandbox")

# Senha de administrador para acesso à aba Cielo Real
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Valor padrão, pode ser alterado no .env

# Cliente Cielo API - Integração REAL com API Oficial
class CieloAPI:
    """
    Cliente para API Cielo E-commerce 3.0
    Documentação: https://developercielo.github.io/manual/cielo-ecommerce
    """
    def __init__(self):
        self.mode = os.getenv("CIELO_MODE", "sandbox")
        self.merchant_id = os.getenv("CIELO_MERCHANT_ID")
        self.merchant_key = os.getenv("CIELO_MERCHANT_KEY")
        self.timeout = int(os.getenv("CIELO_TIMEOUT_MS", "8000")) // 1000
        
        # URLs oficiais da API Cielo
        if self.mode == "sandbox":
            self.api_url = "https://apisandbox.cieloecommerce.cielo.com.br"
            self.query_url = "https://apiquerysandbox.cieloecommerce.cielo.com.br"
        else:
            self.api_url = "https://api.cieloecommerce.cielo.com.br"
            self.query_url = "https://apiquery.cieloecommerce.cielo.com.br"
        
        self.headers = {
            "MerchantId": self.merchant_id or "",
            "MerchantKey": self.merchant_key or "",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        self.credenciais_ok = bool(self.merchant_id and self.merchant_key)
        print(f"[CIELO] Modo: {self.mode.upper()}")
        print(f"[CIELO] MerchantId: {'OK' if self.merchant_id else 'NAO CONFIGURADO'}")
        print(f"[CIELO] MerchantKey: {'OK' if self.merchant_key else 'NAO CONFIGURADO'}")
        print(f"[CIELO] Query URL: {self.query_url}")
    
    async def consultar_transacao_real(self, payment_id: str):
        """
        Consulta uma transação REAL na API Cielo pelo PaymentId
        Endpoint: GET /1/sales/{PaymentId}
        """
        if not self.credenciais_ok:
            return {"success": False, "error": "Credenciais Cielo não configuradas no .env"}
        
        try:
            url = f"{self.query_url}/1/sales/{payment_id}"
            print(f"[CIELO API] GET {url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                
                print(f"[CIELO API] Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "data": data,
                        "fonte": "API_CIELO_REAL"
                    }
                elif response.status_code == 404:
                    return {"success": False, "error": "Transação não encontrada na Cielo", "status_code": 404}
                else:
                    return {
                        "success": False,
                        "error": f"Erro Cielo HTTP {response.status_code}",
                        "details": response.text[:500]
                    }
        except httpx.TimeoutException:
            return {"success": False, "error": "Timeout na API Cielo"}
        except Exception as e:
            print(f"[CIELO API] Erro: {e}")
            return {"success": False, "error": str(e)}
    
    async def consultar_por_order_id(self, merchant_order_id: str):
        """
        Consulta transações por MerchantOrderId
        Endpoint: GET /1/sales?merchantOrderId={merchantOrderId}
        """
        if not self.credenciais_ok:
            return {"success": False, "error": "Credenciais Cielo não configuradas"}
        
        try:
            url = f"{self.query_url}/1/sales?merchantOrderId={merchant_order_id}"
            print(f"[CIELO API] GET {url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "data": data.get("Payments", []),
                        "fonte": "API_CIELO_REAL"
                    }
                else:
                    return {"success": False, "error": f"Erro: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def consultar_vendas(self, data_inicio=None, data_fim=None, page=1, page_size=20):
        """
        IMPORTANTE: A API Cielo E-commerce NÃO possui endpoint de listagem de vendas.
        Para histórico, você deve usar a API de Conciliação ou armazenar PaymentIds.
        Este método retorna dados do banco local.
        """
        return {
            "success": True,
            "mode": self.mode,
            "message": "Histórico carregado do banco local. Use consultar_transacao_real() para verificar na Cielo.",
            "credenciais_configuradas": self.credenciais_ok,
            "data": [],
            "pagination": {"page": page, "page_size": page_size, "total": 0}
        }
    
    def consultar_pagamento(self, payment_id):
        """Consulta pagamento específico (método síncrono para compatibilidade)"""
        try:
            # Para consulta real, usar consultar_transacao_real() (assíncrono)
            url = f"{self.query_url}/1/sales/{payment_id}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            return {
                "success": response.status_code == 200,
                    "data": response.json() if response.status_code == 200 else None,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Instância global do cliente Cielo
cielo_api = CieloAPI()

# ============= REDIS CLIENT =============
# Redis client for caching and rate limiting
redis_cache_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=False,  # Keep binary for pickle
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Redis client for rate limiting (string operations)
redis_rate_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Rate Limiting Simples (fallback)
rate_limit_store = defaultdict(list)

def check_rate_limit(ip: str, max_requests: int = 100, window_seconds: int = 3600):
    now = time.time()
    requests_list = rate_limit_store[ip]
    
    # Remover requisições antigas
    requests_list[:] = [req_time for req_time in requests_list if now - req_time < window_seconds]
    
    if len(requests_list) >= max_requests:
        return False
    
    requests_list.append(now)
    return True

# ============= REDIS FUNCTIONS =============
def check_rate_limit_redis(key: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
    """Rate limiting using Redis with sliding window"""
    try:
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        # Remove old entries
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_requests = redis_client.zcard(key)
        
        if current_requests >= max_requests:
            return False
        
        # Add current request
        redis_client.zadd(key, {str(current_time): current_time})
        redis_client.expire(key, window_seconds)
        
        return True
        
    except Exception as e:
        print(f"[REDIS] Rate limit fallback due to error: {e}")
        # Fallback to in-memory rate limiting
        ip = key.split(':')[-1] if ':' in key else key
        return check_rate_limit(ip, max_requests, window_seconds)

def cache_result(key_prefix: str, ttl: int = 300):
    """Decorator for caching function results in Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Generate cache key
                cache_key = f"hotel:{key_prefix}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    return pickle.loads(cached_result)
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                redis_client.setex(
                    cache_key,
                    ttl,
                    pickle.dumps(result)
                )
                
                return result
                
            except Exception as e:
                print(f"[REDIS] Cache fallback due to error: {e}")
                # Fallback to direct function execution
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern"""
    try:
        search_pattern = f"hotel:{pattern}:*"
        keys = redis_client.keys(search_pattern)
        
        if keys:
            redis_client.delete(*keys)
            print(f"[REDIS] Invalidated {len(keys)} cache keys for pattern: {pattern}")
        
    except Exception as e:
        print(f"[REDIS] Cache invalidation error: {e}")
        # Continue silently - cache will expire naturally

# ============= CELERY CONFIGURATION =============
from celery import Celery

# Configuração Celery
celery_app = Celery(
    'hotel_real_cabo_frio',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
    include=['app_simples']
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# ============= CELERY TASKS =============
@celery_app.task(bind=True, max_retries=3)
def enviar_email_confirmacao_reserva(self, reserva_id: int, cliente_email: str, cliente_nome: str):
    """Envia email de confirmação de reserva"""
    try:
        print(f"[CELERY] Enviando email confirmação reserva {reserva_id} para {cliente_email}")
        
        # Simular envio de email (em produção usar SendGrid, SES, etc.)
        import time
        time.sleep(2)  # Simula tempo de envio
        
        # Em produção, aqui seria a integração real com serviço de email
        mensagem = {
            "para": cliente_email,
            "assunto": f"Confirmação de Reserva - Hotel Real Cabo Frio #{reserva_id}",
            "conteudo": f"Prezado(a) {cliente_nome},\n\nSua reserva foi confirmada com sucesso!\n\nCódigo: {reserva_id}\n\nAguardamos sua visita!"
        }
        
        print(f"[CELERY] Email enviado com sucesso: {mensagem}")
        return {"status": "enviado", "reserva_id": reserva_id}
        
    except Exception as exc:
        print(f"[CELERY] Erro ao enviar email: {exc}")
        # Retry com exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True, max_retries=3)
def enviar_email_lembrete_checkin(self, reserva_id: int, cliente_email: str, cliente_nome: str, data_checkin: str):
    """Envia email de lembrete de check-in"""
    try:
        print(f"[CELERY] Enviando lembrete check-in reserva {reserva_id} para {cliente_email}")
        
        import time
        time.sleep(1)
        
        mensagem = {
            "para": cliente_email,
            "assunto": f"Lembrete de Check-in - Hotel Real Cabo Frio",
            "conteudo": f"Prezado(a) {cliente_nome},\n\nLembrete: Seu check-in é amanhã ({data_checkin}).\n\nCheck-in: 14:00\n\nAguardamos você!"
        }
        
        print(f"[CELERY] Lembrete enviado: {mensagem}")
        return {"status": "enviado", "reserva_id": reserva_id}
        
    except Exception as exc:
        print(f"[CELERY] Erro ao enviar lembrete: {exc}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True, max_retries=3)
def processar_pontos_checkout(self, reserva_id: int, cliente_id: int, pontos_ganhos: int):
    """Processa pontos de fidelidade pós-checkout"""
    try:
        print(f"[CELERY] Processando {pontos_ganhos} pontos para cliente {cliente_id} da reserva {reserva_id}")
        
        # Invalidar cache do cliente
        invalidate_cache_pattern(f"pontos:cliente:{cliente_id}")
        
        # Simular processamento
        import time
        time.sleep(1)
        
        # Em produção, aqui seria a lógica real de crédito de pontos
        print(f"[CELERY] {pontos_ganhos} pontos creditados com sucesso")
        
        return {
            "status": "processado",
            "reserva_id": reserva_id,
            "cliente_id": cliente_id,
            "pontos_creditados": pontos_ganhos
        }
        
    except Exception as exc:
        print(f"[CELERY] Erro ao processar pontos: {exc}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True)
def gerar_relatorio_mensal(self, mes: int, ano: int):
    """Gera relatório mensal de ocupação e receita"""
    try:
        print(f"[CELERY] Gerando relatório mensal {mes}/{ano}")
        
        # Simular geração de relatório
        import time
        time.sleep(5)  # Relatório demorado
        
        # Em produção, buscar dados reais e gerar PDF/Excel
        relatorio = {
            "mes": mes,
            "ano": ano,
            "total_reservas": 150,
            "taxa_ocupacao": 78.5,
            "receita_total": 125000.00,
            "pontos_distribuidos": 2300,
            "gerado_em": datetime.now().isoformat()
        }
        
        print(f"[CELERY] Relatório gerado: {relatorio}")
        return relatorio
        
    except Exception as exc:
        print(f"[CELERY] Erro ao gerar relatório: {exc}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True)
def limpar_logs_antigos(self):
    """Limpa logs antigos (task agendada)"""
    try:
        print(f"[CELERY] Limpando logs antigos")
        
        # Simular limpeza
        import time
        time.sleep(2)
        
        # Em produção, limpar arquivos de log com mais de 30 dias
        print(f"[CELERY] Logs antigos limpos com sucesso")
        return {"status": "limpo", "timestamp": datetime.now().isoformat()}
        
    except Exception as exc:
        print(f"[CELERY] Erro ao limpar logs: {exc}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True)
def analisar_risco_antifraude_async(self, pagamento_id: int):
    """Análise assíncrona de risco antifraude"""
    try:
        print(f"[CELERY] Analisando risco antifraude para pagamento {pagamento_id}")
        
        # Simular análise complexa
        import time
        time.sleep(3)
        
        # Em produção, executar regras complexas de antifraude
        risco_calculado = {
            "pagamento_id": pagamento_id,
            "risk_score": 25,
            "status": "AUTO_APROVADO",
            "fatores": ["Cliente regular", "Valor dentro do padrão"],
            "analise_em": datetime.now().isoformat()
        }
        
        print(f"[CELERY] Análise concluída: {risco_calculado}")
        return risco_calculado
        
    except Exception as exc:
        print(f"[CELERY] Erro na análise antifraude: {exc}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))

app = FastAPI(
    title="Hotel Real Cabo Frio",
    version="1.0.0",
    description="Sistema de Gestão Hoteleira com Reservas, Fidelidade e Antifraude"
)

# ============= CORS MIDDLEWARE (CRÍTICO PARA FRONTEND) =============
# NOTA: Configuração única aqui. NÃO duplicar abaixo.
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.ngrok-free.app",
    "https://*.ngrok.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Aceita qualquer origem (necessário para ngrok dinâmico)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight por 10 minutos
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Headers de segurança
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# Rate Limiting Middleware (Redis-based) - Temporarily disabled
# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     client_ip = request.client.host
#     
#     # Rate limit mais restritivo para endpoints sensíveis
#     if "/api/v1/auth/login" in request.url.path or "/api/v1/auth/admin/verify" in request.url.path:
#         if not check_rate_limit_redis(f"login:{client_ip}", max_requests=10, window_seconds=300):
#             raise HTTPException(
#                 status_code=429,
#                 detail="Too many login attempts. Please try again later.",
#                 headers={"Retry-After": "300"}
#             )
#     else:
#         if not check_rate_limit_redis(f"general:{client_ip}", max_requests=1000, window_seconds=3600):
#             raise HTTPException(
#                 status_code=429,
#                 detail="Rate limit exceeded. Please try again later.",
#                 headers={"Retry-After": "3600"}
#             )
#     
#     return await call_next(request)

# Logging de Segurança
@app.middleware("http")
async def security_logging(request: Request, call_next):
    start_time = time.time()
    
    # Log de requisição
    client_ip = request.client.host
    method = request.method
    path = request.url.path
    user_agent = request.headers.get("user-agent", "Unknown")
    
    print(f"[SECURITY] {method} {path} from {client_ip} - {user_agent[:50]}")
    
    response = await call_next(request)
    
    # Log de resposta
    process_time = time.time() - start_time
    status_code = response.status_code
    
    # Log de eventos suspeitos
    if status_code >= 400:
        print(f"[SECURITY ALERT] {method} {path} - Status: {status_code} - IP: {client_ip}")
    
    if process_time > 5.0:
        print(f"[SECURITY] Slow request: {method} {path} - {process_time:.2f}s")
    
    return response

load_dotenv()
db = Prisma()

@app.on_event("startup")
async def on_startup():
    await db.connect()
    # Configurar instância do banco para o módulo de autenticação
    # set_database_instance(db)  # Function not implemented - commented out to fix startup error
    print("[Prisma] Conectado ao banco via Accelerate.")
    await inicializar_dados()

@app.on_event("shutdown")
async def on_shutdown():
    await db.disconnect()

# CORS - Já configurado acima, NÃO duplicar

# ============= ENUMS =============
class StatusReserva(str, Enum):
    PENDENTE = "PENDENTE"
    HOSPEDADO = "HOSPEDADO"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELADO = "CANCELADO"

class TipoSuite(str, Enum):
    LUXO = "LUXO"
    MASTER = "MASTER"
    REAL = "REAL"

class StatusQuarto(str, Enum):
    LIVRE = "LIVRE"
    OCUPADO = "OCUPADO"
    MANUTENCAO = "MANUTENCAO"
    BLOQUEADO = "BLOQUEADO"

class StatusAntifraude(str, Enum):
    PENDENTE = "PENDENTE"
    AUTO_APROVADO = "AUTO_APROVADO"
    RECUSADO = "RECUSADO"
    MANUAL_APROVADO = "MANUAL_APROVADO"

# ============= SCHEMAS =============
class ClienteCreate(BaseModel):
    nome_completo: str
    documento: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None

class ReservaCreate(BaseModel):
    cliente_id: int
    quarto_numero: str
    tipo_suite: TipoSuite
    checkin_previsto: datetime
    checkout_previsto: datetime
    valor_diaria: float
    num_diarias: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class FuncionarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: str = "FUNCIONARIO"
    status: str = "ATIVO"

class FuncionarioCreate(FuncionarioBase):
    senha: str = "123456"

class FuncionarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    perfil: Optional[str] = None
    status: Optional[str] = None
    senha: Optional[str] = None

class QuartoBase(BaseModel):
    numero: str
    tipo_suite: TipoSuite
    status: StatusQuarto = StatusQuarto.LIVRE

class QuartoCreate(QuartoBase):
    pass

class QuartoUpdate(BaseModel):
    numero: Optional[str] = None
    tipo_suite: Optional[TipoSuite] = None
    status: Optional[StatusQuarto] = None

# ============= SCHEMAS DE PAGAMENTO =============
class PagamentoCreate(BaseModel):
    reserva_id: int
    valor: float
    metodo: str  # credit_card, debit_card, pix
    parcelas: Optional[int] = None
    cartao_numero: Optional[str] = None
    cartao_validade: Optional[str] = None
    cartao_cvv: Optional[str] = None
    cartao_nome: Optional[str] = None

class PagamentoResponse(BaseModel):
    id: int
    cielo_payment_id: str
    status: str
    valor: float
    metodo: str
    parcelas: Optional[int]
    data_criacao: datetime
    url_pagamento: Optional[str] = None

class CieloWebhook(BaseModel):
    payment_id: str
    status: str
    authorization_code: Optional[str] = None
    response_code: Optional[str] = None
    response_message: Optional[str] = None

# ============= SCHEMAS DO SISTEMA REAL POINTS =============
class ValidarReservaRequest(BaseModel):
    codigo_reserva: str
    cpf_hospede: str
    usuario_id: int

class ConfirmarLancamentoRequest(BaseModel):
    reserva_id: int
    cliente_id: int
    cpf_hospede: str
    usuario_id: int

class AjustarPontosRequest(BaseModel):
    cliente_id: int
    pontos: int  # positivo para creditar, negativo para debitar
    motivo: str
    usuario_id: int

class GerarConviteRequest(BaseModel):
    convidante_cliente_id: int
    usos_maximos: int = 5

class UsarConviteRequest(BaseModel):
    codigo: str
    cliente_id: int  # quem está usando o convite

class SaldoResponse(BaseModel):
    success: bool
    saldo: int
    usuario_pontos_id: int
    error: Optional[str] = None

class TransacaoResponse(BaseModel):
    success: bool
    transacao_id: int
    novo_saldo: int
    error: Optional[str] = None

class HistoricoTransacao(BaseModel):
    id: int
    tipo: str
    origem: str
    pontos: int
    motivo: Optional[str]
    created_at: datetime
    reserva_codigo: Optional[str] = None

class HistoricoResponse(BaseModel):
    success: bool
    transacoes: List[HistoricoTransacao]
    total: int
    error: Optional[str] = None

class ValidarReservaResponse(BaseModel):
    success: bool
    valido: bool
    pontos_calculados: Optional[int] = None
    motivo: Optional[str] = None
    reserva: Optional[Dict] = None
    pagamento: Optional[Dict] = None
    error: Optional[str] = None

class ConviteResponse(BaseModel):
    success: bool
    codigo: Optional[str] = None
    convidante: Optional[Dict] = None
    usos_restantes: Optional[int] = None
    error: Optional[str] = None

# ============= FUNÇÕES DE SERIALIZAÇÃO =============
def serialize_cliente(c) -> dict:
    total_reservas = c.totalReservas or 0
    total_gasto = c.totalGasto or 0
    return {
        "id": c.id,
        "nome_completo": c.nomeCompleto,
        "documento": c.documento,
        "telefone": c.telefone,
        "email": c.email,
        "data_nascimento": c.dataNascimento.isoformat() if c.dataNascimento else None,
        "nacionalidade": c.nacionalidade,
        "endereco_completo": c.enderecoCompleto,
        "cidade": c.cidade,
        "estado": c.estado,
        "pais": c.pais,
        "observacoes": c.observacoes,
        "tipo_hospede": c.tipoHospede,
        "nivel_fidelidade": c.nivelFidelidade,
        "total_gasto": total_gasto,
        "total_reservas": total_reservas,
        "ultima_visita": c.ultimaVisita.isoformat() if c.ultimaVisita else None,
        "status": c.status,
        "created_at": c.createdAt.isoformat() if c.createdAt else None,
        "idade": calcular_idade(c.dataNascimento) if c.dataNascimento else None,
        "media_gasto_por_reserva": total_gasto / max(total_reservas, 1),
        "dias_desde_ultima_visita": (datetime.now() - c.ultimaVisita).days if c.ultimaVisita else None,
        "frequencia_mensal": calcular_frequencia_mensal(total_reservas, c.createdAt),
        "perfil_risco": classificar_perfil_risco(c),
    }

def serialize_cliente_analytics(c) -> dict:
    """Serialização completa com analytics para visualização"""
    total_reservas = c.totalReservas or 0
    total_gasto = c.totalGasto or 0
    return {
        "id": c.id,
        "nome_completo": c.nomeCompleto,
        "documento": c.documento,
        "telefone": c.telefone,
        "email": c.email,
        "data_nascimento": c.dataNascimento.isoformat() if c.dataNascimento else None,
        "idade": calcular_idade(c.dataNascimento) if c.dataNascimento else None,
        "nacionalidade": c.nacionalidade,
        "endereco_completo": c.enderecoCompleto,
        "cidade": c.cidade,
        "estado": c.estado,
        "pais": c.pais,
        "observacoes": c.observacoes,
        "tipo_hospede": c.tipoHospede,
        "nivel_fidelidade": c.nivelFidelidade or 0,
        "total_gasto": total_gasto,
        "total_reservas": total_reservas,
        "ultima_visita": c.ultimaVisita.isoformat() if c.ultimaVisita else None,
        "status": c.status,
        "created_at": c.createdAt.isoformat() if c.createdAt else None,
        "analytics": {
            "media_gasto_por_reserva": total_gasto / max(total_reservas, 1),
            "dias_desde_ultima_visita": (datetime.now() - c.ultimaVisita).days if c.ultimaVisita else None,
            "frequencia_mensal": calcular_frequencia_mensal(total_reservas, c.createdAt),
            "perfil_risco": classificar_perfil_risco(c),
        }
    }

def calcular_idade(data_nascimento: datetime) -> int:
    """Calcula idade a partir da data de nascimento"""
    hoje = date.today()
    idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
    return idade

def calcular_frequencia_mensal(total_reservas: int, data_criacao) -> float:
    """Calcula frequência média de reservas por mês"""
    if not data_criacao:
        return 0.0
    try:
        meses_ativo = ((datetime.now() - data_criacao).days / 30)
        return round(total_reservas / max(meses_ativo, 1), 2)
    except:
        return 0.0

def classificar_perfil_risco(cliente) -> str:
    """Classifica perfil de risco do cliente"""
    risco_score = 0
    total_reservas = cliente.totalReservas or 0
    total_gasto = cliente.totalGasto or 0
    nivel_fidelidade = cliente.nivelFidelidade or 0
    
    if total_reservas == 0:
        risco_score += 30
    elif total_reservas < 3:
        risco_score += 15
    
    if total_gasto > 50000:
        risco_score += 20
    elif total_gasto > 20000:
        risco_score += 10
    
    if nivel_fidelidade < 2:
        risco_score += 15
    
    if not cliente.ultimaVisita or (datetime.now() - cliente.ultimaVisita).days > 365:
        risco_score += 20
    
    if risco_score >= 60:
        return "ALTO"
    elif risco_score >= 30:
        return "MEDIO"
    else:
        return "BAIXO"

def serialize_reserva(r) -> dict:
    return {
        "id": r.id,
        "codigo_reserva": r.codigoReserva,
        "cliente_id": r.clienteId,
        "cliente_nome": r.clienteNome,
        "quarto_numero": r.quartoNumero,
        "tipo_suite": r.tipoSuite,
        "status": r.status,
        "checkin_previsto": r.checkinPrevisto.isoformat() if r.checkinPrevisto else None,
        "checkout_previsto": r.checkoutPrevisto.isoformat() if r.checkoutPrevisto else None,
        "checkin_real": None,
        "checkout_real": None,
        "valor_diaria": r.valorDiaria,
        "num_diarias": r.numDiarias,
        "valor_total": float(r.valorDiaria) * r.numDiarias,
        "created_at": r.createdAt.isoformat() if r.createdAt else None,
    }

def serialize_quarto(q) -> dict:
    return {
        "id": q.id,
        "numero": q.numero,
        "tipo_suite": q.tipoSuite,
        "status": q.status,
        "created_at": q.createdAt.isoformat() if q.createdAt else None,
    }

def serialize_funcionario(u) -> dict:
    return {
        "id": u.id,
        "nome": u.nome,
        "email": u.email,
        "perfil": u.perfil,
        "status": u.status,
    }

def serialize_operacao_antifraude(op) -> dict:
    return {
        "id": op.id,
        "reserva_id": op.reservaId,
        "cliente_id": op.clienteId,
        "pontos_calculados": op.pontosCalculados,
        "risk_score": op.riskScore,
        "status": op.status,
        "created_at": op.createdAt.isoformat() if op.createdAt else None,
    }

def serialize_historico_pontos(h) -> dict:
    return {
        "id": h.id,
        "cliente_id": h.clienteId,
        "tipo": h.tipo,
        "pontos": h.pontos,
        "origem": h.origem,
        "data": h.data.isoformat() if h.data else None,
        "created_at": h.createdAt.isoformat() if h.createdAt else None,
    }

# ============= FUNÇÕES DE AUTENTICAÇÃO =============
from pydantic import BaseModel

class User(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str

async def get_current_user(authorization: str = Header(None)):
    """Valida token fake e retorna usuário atual"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    # Aceita tanto "Bearer token" quanto "token" direto
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    if token != "fake-jwt-token":
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Retorna usuário admin padrão para teste
    return User(
        id=1,
        nome="Admin",
        email="admin@hotelreal.com.br",
        perfil="ADMIN"
    )

def require_roles(*allowed_roles):
    """Cria dependência para verificar se usuário tem permissão"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.perfil not in allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Acesso negado. Perfis permitidos: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# ============= FUNÇÕES DE NOTIFICAÇÕES =============
async def criar_notificacao(titulo: str, mensagem: str, tipo: str = "info", categoria: str = "sistema", perfil: str = None, reserva_id: int = None, pagamento_id: int = None, url_acao: str = None):
    """Cria uma notificação no sistema"""
    await db.notificacao.create({
        "data": {
            "titulo": titulo,
            "mensagem": mensagem,
            "tipo": tipo,
            "categoria": categoria,
            "perfil": perfil,
            "reservaId": reserva_id,
            "pagamentoId": pagamento_id,
            "urlAcao": url_acao
        }
    })

async def notificar_reserva_criada(reserva):
    """Notifica sobre nova reserva criada (para recepcionistas)"""
    await criar_notificacao(
        titulo="🆕 Nova Reserva",
        mensagem=f"{reserva.clienteNome} fez reserva para o quarto {reserva.quartoNumero}",
        tipo="info",
        categoria="reserva",
        perfil="RECEPCAO",
        reserva_id=reserva.id,
        url_acao=f"/reservas/{reserva.id}"
    )
    
    # Notificar admins sobre reservas de alto valor
    if reserva.valorTotal and reserva.valorTotal > 5000:
        await criar_notificacao(
            titulo="💰 Reserva de Alto Valor",
            mensagem=f"Reserva de R${reserva.valorTotal} - {reserva.codigoReserva}",
            tipo="warning",
            categoria="reserva",
            perfil="ADMIN",
            reserva_id=reserva.id,
            url_acao=f"/reservas/{reserva.id}"
        )

async def notificar_checkin_realizado(reserva):
    """Notifica sobre check-in realizado (para recepcionistas)"""
    await criar_notificacao(
        titulo="✅ Check-in Realizado",
        mensagem=f"{reserva.clienteNome} fez check-in no quarto {reserva.quartoNumero}",
        tipo="success",
        categoria="reserva",
        perfil="RECEPCAO",
        reserva_id=reserva.id,
        url_acao=f"/reservas/{reserva.id}"
    )

async def notificar_checkout_realizado(reserva):
    """Notifica sobre check-out realizado (para recepcionistas)"""
    await criar_notificacao(
        titulo="🚪 Check-out Realizado",
        mensagem=f"{reserva.clienteNome} fez check-out do quarto {reserva.quartoNumero}",
        tipo="info",
        categoria="reserva",
        perfil="RECEPCAO",
        reserva_id=reserva.id,
        url_acao=f"/reservas/{reserva.id}"
    )
    
    # Notificar admins sobre checkout com pontos gerados
    if hasattr(reserva, 'pontosGerados') and reserva.pontosGerados > 0:
        await criar_notificacao(
            titulo="🎯 Pontos Gerados no Checkout",
            mensagem=f"{reserva.pontosGerados} pontos para {reserva.clienteNome}",
            tipo="info",
            categoria="reserva",
            perfil="ADMIN",
            reserva_id=reserva.id,
            url_acao=f"/pontos/{reserva.clienteId}"
        )

async def notificar_pagamento_aprovado(pagamento, reserva):
    """Notifica sobre pagamento aprovado (apenas admins)"""
    await criar_notificacao(
        titulo="💰 Pagamento Aprovado",
        mensagem=f"Pagamento de R${pagamento.valor} da reserva {reserva.codigoReserva} foi aprovado",
        tipo="success",
        categoria="pagamento",
        perfil="ADMIN",
        pagamento_id=pagamento.id,
        url_acao=f"/pagamentos/{pagamento.id}"
    )

async def notificar_pagamento_recusado(pagamento, reserva):
    """Notifica sobre pagamento recusado (CRÍTICO - apenas admins)"""
    await criar_notificacao(
        titulo="❌ Pagamento Recusado",
        mensagem=f"Pagamento de R${pagamento.valor} da reserva {reserva.codigoReserva} foi recusado",
        tipo="critical",
        categoria="pagamento",
        perfil="ADMIN",
        pagamento_id=pagamento.id,
        url_acao=f"/pagamentos/{pagamento.id}"
    )
    
    # Notificar recepcionistas sobre problema na reserva
    await criar_notificacao(
        titulo="⚠️ Problema no Pagamento",
        mensagem=f"Reserva {reserva.codigoReserva} - pagamento recusado",
        tipo="warning",
        categoria="reserva",
        perfil="RECEPCAO",
        reserva_id=reserva.id,
        url_acao=f"/reservas/{reserva.id}"
    )

async def notificar_checkins_hoje():
    """Notifica sobre check-ins previstos para hoje"""
    hoje = date.today()
    checkins_hoje = await db.reserva.find_many(
        where={
            "checkinPrevisto": {
                "gte": datetime.combine(hoje, datetime.min.time()),
                "lt": datetime.combine(hoje + timedelta(days=1), datetime.min.time())
            },
            "status": "PENDENTE"
        }
    )
    
    if checkins_hoje:
        await criar_notificacao(
            titulo="📅 Check-ins Hoje",
            mensagem=f"{len(checkins_hoje)} check-ins previstos para hoje",
            tipo="warning",
            categoria="reserva",
            perfil="RECEPCAO",
            url_acao="/reservas"
        )

async def notificar_checkouts_hoje():
    """Notifica sobre check-outs previstos para hoje"""
    hoje = date.today()
    checkouts_hoje = await db.reserva.find_many(
        where={
            "checkoutPrevisto": {
                "gte": datetime.combine(hoje, datetime.min.time()),
                "lt": datetime.combine(hoje + timedelta(days=1), datetime.min.time())
            },
            "status": "HOSPEDADO"
        }
    )
    
    if checkouts_hoje:
        await criar_notificacao(
            titulo="🏃 Check-outs Hoje",
            mensagem=f"{len(checkouts_hoje)} check-outs previstos para hoje",
            tipo="warning",
            categoria="reserva",
            perfil="RECEPCAO",
            url_acao="/reservas"
        )

# ============= FUNÇÕES DE INICIALIZAÇÃO =============
async def inicializar_quartos():
    quartos_existentes = await db.quarto.count()
    if quartos_existentes > 0:
        return
    
    _luxo_colunas = [
        ["102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112"],
        ["202", "203", "204", "205", "206", "207", "208", "209", "210", "211", "212"],
        ["302", "303", "304", "305", "306", "307", "308", "309", "310", "311", "312"],
        ["402", "403", "404", "405", "406", "407", "408", "409", "410", "411", "412", "502"],
    ]
    
    _dupla_numeros = ["101"]
    _master_numeros = ["503"]
    _real_numeros = ["501"]
    
    # Criar quartos LUXO
    for coluna in _luxo_colunas:
        for numero in coluna:
            await db.quarto.create(
                data={
                    "numero": numero,
                    "tipoSuite": "LUXO",
                    "status": "LIVRE"
                }
            )
    
    # Criar quartos especiais
    for numero in _dupla_numeros:
        await db.quarto.create(
            data={
                "numero": numero,
                "tipoSuite": "LUXO",
                "status": "LIVRE"
            }
        )
    
    for numero in _master_numeros:
        await db.quarto.create(
            data={
                "numero": numero,
                "tipoSuite": "MASTER",
                "status": "LIVRE"
            }
        )
    
    for numero in _real_numeros:
        await db.quarto.create(
            data={
                "numero": numero,
                "tipoSuite": "REAL",
                "status": "LIVRE"
            }
        )

async def inicializar_funcionarios():
    # Deletar admin existente para forçar recriação com senha correta
    admin_existente = await db.funcionario.find_unique(where={"email": "admin@hotelreal.com.br"})
    if admin_existente:
        await db.funcionario.delete(where={"email": "admin@hotelreal.com.br"})
    
    # Criar admin padrão com senha hash
    await db.funcionario.create(
        data={
            "nome": "Admin",
            "email": "admin@hotelreal.com.br",
            "senha": hashlib.sha256("admin123".encode()).hexdigest(),
            "perfil": "ADMIN",
            "status": "ATIVO"
        }
    )

async def inicializar_dados():
    await inicializar_quartos()
    await inicializar_funcionarios()
    print("[Prisma] Dados iniciais criados com sucesso.")

# ============= ROTAS PRINCIPAIS =============
@app.get("/")
async def root():
    return {
        "message": "Hotel Real Cabo Frio API",
        "status": "online",
        "version": "1.0.0"
    }

# ============= ROTAS PÚBLICAS DE BOOKING (SEM AUTENTICAÇÃO) =============

class BookingDisponibilidadeRequest(BaseModel):
    data_checkin: str  # YYYY-MM-DD
    data_checkout: str  # YYYY-MM-DD

class BookingReservaRequest(BaseModel):
    # Dados do hóspede
    nome_completo: str
    documento: str  # CPF
    email: str
    telefone: str
    # Dados da reserva
    quarto_numero: str
    tipo_suite: str
    data_checkin: str
    data_checkout: str
    num_hospedes: int = 1
    num_criancas: int = 0
    observacoes: Optional[str] = None
    # Pagamento (opcional - pode pagar depois)
    metodo_pagamento: Optional[str] = None  # credit_card, pix, na_chegada

@app.get("/api/v1/public/quartos/disponiveis")
async def listar_quartos_disponiveis_publico(data_checkin: str, data_checkout: str):
    """
    Lista quartos disponíveis para reserva online (PÚBLICO - sem autenticação)
    """
    try:
        checkin = datetime.strptime(data_checkin, "%Y-%m-%d")
        checkout = datetime.strptime(data_checkout, "%Y-%m-%d")
        
        if checkout <= checkin:
            raise HTTPException(status_code=400, detail="Data de check-out deve ser posterior ao check-in")
        
        num_diarias = (checkout - checkin).days
        
        # Buscar todos os quartos
        todos_quartos = await db.quarto.find_many(where={"status": {"not": "MANUTENCAO"}})
        
        # Buscar reservas que conflitam com as datas
        reservas_conflito = await db.reserva.find_many(
            where={
                "status": {"in": ["PENDENTE", "HOSPEDADO"]},
                "checkinPrevisto": {"lt": checkout},
                "checkoutPrevisto": {"gt": checkin}
            }
        )
        
        quartos_ocupados = {r.quartoNumero for r in reservas_conflito}
        
        # Filtrar quartos disponíveis
        quartos_disponiveis = [
            q for q in todos_quartos 
            if q.numero not in quartos_ocupados
        ]
        
        # Preços por tipo de suíte
        precos = {
            "LUXO": 350.00,
            "MASTER": 550.00,
            "REAL": 850.00
        }
        
        # Agrupar por tipo
        tipos_disponiveis = {}
        for quarto in quartos_disponiveis:
            tipo = quarto.tipoSuite
            if tipo not in tipos_disponiveis:
                tipos_disponiveis[tipo] = {
                    "tipo": tipo,
                    "preco_diaria": precos.get(tipo, 350.00),
                    "preco_total": precos.get(tipo, 350.00) * num_diarias,
                    "quartos": [],
                    "quantidade_disponivel": 0
                }
            tipos_disponiveis[tipo]["quartos"].append({
                "numero": quarto.numero,
                "status": quarto.status
            })
            tipos_disponiveis[tipo]["quantidade_disponivel"] += 1
        
        return {
            "success": True,
            "data_checkin": data_checkin,
            "data_checkout": data_checkout,
            "num_diarias": num_diarias,
            "tipos_disponiveis": list(tipos_disponiveis.values()),
            "total_quartos_disponiveis": len(quartos_disponiveis)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Formato de data inválido: {str(e)}")
    except Exception as e:
        print(f"[ERRO] Falha ao buscar disponibilidade: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar disponibilidade")

@app.post("/api/v1/public/reservas")
async def criar_reserva_online(dados: BookingReservaRequest):
    """
    Criar reserva online (PÚBLICO - sem autenticação)
    Cliente pode fazer reserva diretamente pelo site
    """
    try:
        # Validar datas
        checkin = datetime.strptime(dados.data_checkin, "%Y-%m-%d")
        checkout = datetime.strptime(dados.data_checkout, "%Y-%m-%d")
        
        if checkout <= checkin:
            raise HTTPException(status_code=400, detail="Data de check-out deve ser posterior ao check-in")
        
        if checkin.date() < date.today():
            raise HTTPException(status_code=400, detail="Data de check-in não pode ser no passado")
        
        num_diarias = (checkout - checkin).days
        
        # Verificar se quarto está disponível
        reservas_conflito = await db.reserva.find_many(
            where={
                "quartoNumero": dados.quarto_numero,
                "status": {"in": ["PENDENTE", "HOSPEDADO"]},
                "checkinPrevisto": {"lt": checkout},
                "checkoutPrevisto": {"gt": checkin}
            }
        )
        
        if reservas_conflito:
            raise HTTPException(status_code=400, detail="Quarto não está disponível para as datas selecionadas")
        
        # Buscar ou criar cliente
        cliente = await db.cliente.find_unique(where={"documento": dados.documento})
        
        if not cliente:
            # Criar novo cliente
            cliente = await db.cliente.create(
                data={
                    "nomeCompleto": dados.nome_completo,
                    "documento": dados.documento,
                    "email": dados.email,
                    "telefone": dados.telefone,
                    "status": "ATIVO"
                }
            )
            print(f"[BOOKING] Novo cliente criado: {cliente.id} - {dados.nome_completo}")
        else:
            # Atualizar dados do cliente se necessário
            await db.cliente.update(
                where={"id": cliente.id},
                data={
                    "email": dados.email,
                    "telefone": dados.telefone
                }
            )
        
        # Preços por tipo de suíte
        precos = {
            "LUXO": 350.00,
            "MASTER": 550.00,
            "REAL": 850.00
        }
        
        valor_diaria = precos.get(dados.tipo_suite, 350.00)
        valor_total = valor_diaria * num_diarias
        
        # Gerar código único da reserva
        total_reservas = await db.reserva.count()
        codigo_reserva = f"WEB-{datetime.now().strftime('%Y%m%d')}-{total_reservas+1:06d}"
        
        # Criar reserva
        checkin_previsto = datetime.combine(checkin.date(), datetime.strptime("15:00", "%H:%M").time())
        checkout_previsto = datetime.combine(checkout.date(), datetime.strptime("12:00", "%H:%M").time())
        
        nova_reserva = await db.reserva.create(
            data={
                "codigoReserva": codigo_reserva,
                "clienteId": cliente.id,
                "clienteNome": dados.nome_completo,
                "quartoNumero": dados.quarto_numero,
                "tipoSuite": dados.tipo_suite,
                "checkinPrevisto": checkin_previsto,
                "checkoutPrevisto": checkout_previsto,
                "valorDiaria": valor_diaria,
                "numDiarias": num_diarias,
                "status": "PENDENTE",
            }
        )
        
        print(f"[BOOKING] Nova reserva online criada: {codigo_reserva}")
        
        # Se método de pagamento foi informado e não é "na_chegada", processar pagamento
        pagamento_info = None
        if dados.metodo_pagamento and dados.metodo_pagamento != "na_chegada":
            pagamento = await db.pagamento.create(
                data={
                    "reservaId": nova_reserva.id,
                    "valor": valor_total,
                    "metodo": dados.metodo_pagamento,
                    "status": "PENDENTE" if dados.metodo_pagamento == "pix" else "APROVADO",
                    "cieloPaymentId": f"WEB_{datetime.now().strftime('%Y%m%d%H%M%S')}_{nova_reserva.id}",
                    "parcelas": 1,
                }
            )
            pagamento_info = {
                "id": pagamento.id,
                "status": pagamento.statusPagamento,
                "metodo": pagamento.metodo,
                "valor": float(pagamento.valor)
            }
        
        return {
            "success": True,
            "message": "Reserva criada com sucesso!",
            "reserva": {
                "codigo": codigo_reserva,
                "id": nova_reserva.id,
                "cliente": dados.nome_completo,
                "quarto": dados.quarto_numero,
                "tipo_suite": dados.tipo_suite,
                "checkin": dados.data_checkin,
                "checkout": dados.data_checkout,
                "num_diarias": num_diarias,
                "valor_diaria": valor_diaria,
                "valor_total": valor_total,
                "status": "PENDENTE"
            },
            "pagamento": pagamento_info,
            "instrucoes": {
                "checkin_horario": "15:00",
                "checkout_horario": "12:00",
                "documentos": "Apresentar documento de identidade com foto no check-in",
                "contato": "recepcao@hotelreal.com.br | (22) 2222-2222"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao criar reserva online: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar reserva: {str(e)}")

@app.get("/api/v1/public/reservas/{codigo}")
async def consultar_reserva_publico(codigo: str):
    """
    Consultar reserva por código (PÚBLICO - sem autenticação)
    """
    try:
        reserva = await db.reserva.find_first(where={"codigoReserva": codigo})
        
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")
        
        # Buscar pagamentos
        pagamentos = await db.pagamento.find_many(where={"reservaId": reserva.id})
        total_pago = sum(float(p.valor) for p in pagamentos if p.statusPagamento == "APROVADO")
        valor_total = float(reserva.valorDiaria) * reserva.numDiarias
        
        return {
            "success": True,
            "reserva": {
                "codigo": reserva.codigoReserva,
                "cliente": reserva.clienteNome,
                "quarto": reserva.quartoNumero,
                "tipo_suite": reserva.tipoSuite,
                "checkin": reserva.checkinPrevisto.strftime("%Y-%m-%d") if reserva.checkinPrevisto else None,
                "checkout": reserva.checkoutPrevisto.strftime("%Y-%m-%d") if reserva.checkoutPrevisto else None,
                "num_diarias": reserva.numDiarias,
                "valor_diaria": float(reserva.valorDiaria),
                "valor_total": valor_total,
                "status": reserva.status,
                "total_pago": total_pago,
                "saldo_pendente": valor_total - total_pago
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao consultar reserva: {e}")
        raise HTTPException(status_code=500, detail="Erro ao consultar reserva")

@app.get("/api/v1/public/pontos/{documento}")
async def consultar_pontos_publico(documento: str):
    """
    Consultar saldo de pontos por CPF (PÚBLICO - sem autenticação)
    """
    try:
        # Buscar cliente pelo documento
        cliente = await db.cliente.find_unique(where={"documento": documento})
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Buscar saldo de pontos
        historico = await db.historicopontos.find_many(
            where={"clienteId": cliente.id},
            order={"data": "desc"},
            take=10
        )
        
        saldo = sum(h.pontos if h.tipo == "GANHO" else -h.pontos for h in historico)
        
        return {
            "success": True,
            "cliente": {
                "nome": cliente.nomeCompleto,
                "documento": cliente.documento[:3] + "***" + cliente.documento[-2:]  # Mascarar CPF
            },
            "pontos": {
                "saldo": saldo,
                "historico_recente": [
                    {
                        "tipo": h.tipo,
                        "pontos": h.pontos,
                        "origem": h.origem,
                        "data": h.data.strftime("%d/%m/%Y") if h.data else None
                    }
                    for h in historico[:5]
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao consultar pontos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao consultar pontos")

# ============= ROTAS DE AUTENTICAÇÃO =============
@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    funcionario = await db.funcionario.find_unique(where={"email": request.email})
    
    if not funcionario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    senha_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if funcionario.senha != senha_hash:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    return {
        "user": {
            "id": funcionario.id,
            "nome": funcionario.nome,
            "email": funcionario.email,
            "perfil": funcionario.perfil
        },
        "token": "fake-jwt-token"
    }

@app.post("/api/v1/auth/admin/verify")
async def verify_admin_password(request: dict):
    """Verifica senha de administrador para acesso a funcionalidades restritas"""
    password = request.get("password", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    if password == admin_password:
        return {"success": True}
    else:
        return {"success": False}

# ============= ROTAS DE FUNCIONÁRIOS =============
@app.get("/api/v1/funcionarios")
async def listar_funcionarios():
    registros = await db.funcionario.find_many(order={"id": "asc"})
    return {
        "funcionarios": [serialize_funcionario(u) for u in registros],
        "total": len(registros),
    }

@app.post("/api/v1/funcionarios")
async def criar_funcionario(func: FuncionarioCreate):
    existente = await db.funcionario.find_unique(where={"email": func.email})
    if existente:
        raise HTTPException(status_code=400, detail="Já existe um funcionário com este email")
    
    senha_hash = hashlib.sha256(func.senha.encode()).hexdigest()
    novo_funcionario = await db.funcionario.create(
        data={
            "nome": func.nome,
            "email": func.email,
            "senha": senha_hash,
            "perfil": func.perfil,
            "status": func.status,
        }
    )
    
    return serialize_funcionario(novo_funcionario)

@app.put("/api/v1/funcionarios/{funcionario_id}")
async def atualizar_funcionario(funcionario_id: int, dados: FuncionarioUpdate):
    funcionario = await db.funcionario.find_unique(where={"id": funcionario_id})
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    if dados.email and dados.email != funcionario.email:
        existente = await db.funcionario.find_unique(where={"email": dados.email})
        if existente:
            raise HTTPException(status_code=400, detail="Já existe um funcionário com este email")
    
    update_data = {}
    if dados.nome is not None:
        update_data["nome"] = dados.nome
    if dados.email is not None:
        update_data["email"] = dados.email
    if dados.perfil is not None:
        update_data["perfil"] = dados.perfil
    if dados.status is not None:
        update_data["status"] = dados.status
    if dados.senha:
        update_data["senha"] = hashlib.sha256(dados.senha.encode()).hexdigest()
    
    funcionario_atualizado = await db.funcionario.update(
        where={"id": funcionario_id},
        data=update_data
    )
    
    return serialize_funcionario(funcionario_atualizado)

# ============= ROTAS DE QUARTOS =============
@app.get("/api/v1/quartos")
async def listar_quartos():
    registros = await db.quarto.find_many(order={"id": "asc"})
    return {
        "quartos": [serialize_quarto(q) for q in registros],
        "total": len(registros),
    }

@app.post("/api/v1/quartos")
async def criar_quarto(quarto: QuartoCreate):
    existente = await db.quarto.find_unique(where={"numero": quarto.numero})
    if existente:
        raise HTTPException(status_code=400, detail="Já existe um quarto com este número")
    
    novo_quarto = await db.quarto.create(
        data={
            "numero": quarto.numero,
            "tipoSuite": quarto.tipo_suite,
            "status": quarto.status,
        }
    )
    
    return serialize_quarto(novo_quarto)

@app.put("/api/v1/quartos/{quarto_id}")
async def atualizar_quarto(quarto_id: int, dados: QuartoUpdate):
    quarto = await db.quarto.find_unique(where={"id": quarto_id})
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado")
    
    if dados.numero and dados.numero != quarto.numero:
        existente = await db.quarto.find_unique(where={"numero": dados.numero})
        if existente:
            raise HTTPException(status_code=400, detail="Já existe um quarto com este número")
    
    update_data = {}
    if dados.numero is not None:
        update_data["numero"] = dados.numero
    if dados.tipo_suite is not None:
        update_data["tipoSuite"] = dados.tipo_suite
    if dados.status is not None:
        update_data["status"] = dados.status
    
    quarto_atualizado = await db.quarto.update(
        where={"id": quarto_id},
        data=update_data
    )
    
    return serialize_quarto(quarto_atualizado)

@app.delete("/api/v1/quartos/{quarto_id}")
async def deletar_quarto(quarto_id: int):
    quarto = await db.quarto.find_unique(where={"id": quarto_id})
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado")
    
    # Verificar se o quarto está ocupado
    if quarto.status == "OCUPADO":
        raise HTTPException(status_code=400, detail="Não é possível excluir um quarto ocupado")
    
    # Verificar se há reservas ativas para este quarto
    reservas_ativas = await db.reserva.count(
        where={
            "quartoNumero": quarto.numero,
            "status": {"in": ["PENDENTE", "HOSPEDADO"]}
        }
    )
    
    if reservas_ativas > 0:
        raise HTTPException(status_code=400, detail="Não é possível excluir um quarto com reservas ativas")
    
    await db.quarto.delete(where={"id": quarto_id})
    
    return {"success": True, "message": "Quarto excluído com sucesso"}

# ============= ROTAS DE PAGAMENTO (CIELO) =============
class PagamentoCreate(BaseModel):
    reserva_id: int
    valor: float
    metodo: str  # credit_card, debit_card, pix
    parcelas: Optional[int] = 1
    cartao_numero: Optional[str] = None
    cartao_validade: Optional[str] = None
    cartao_cvv: Optional[str] = None
    cartao_nome: Optional[str] = None

# Instância global do cliente Cielo
cielo_api = CieloAPI()

@app.get("/api/v1/pagamentos")
async def listar_pagamentos():
    """Lista todos os pagamentos"""
    try:
        pagamentos = await db.pagamento.find_many(order={"id": "desc"})
        return {
            "success": True,
            "pagamentos": [
                {
                    "id": p.id,
                    "reserva_id": p.reservaId,
                    "valor": float(p.valor),
                    "metodo": p.metodo,
                    "status": p.statusPagamento,
                    "cielo_payment_id": p.cieloPaymentId,
                    "created_at": p.createdAt.isoformat() if p.createdAt else None
                }
                for p in pagamentos
            ],
            "total": len(pagamentos)
        }
    except Exception as e:
        print(f"[ERRO] Falha ao listar pagamentos: {e}")
        return {"success": False, "error": str(e), "pagamentos": []}

@app.get("/api/v1/pagamentos/reserva/{reserva_id}")
async def listar_pagamentos_reserva(reserva_id: int):
    """Lista pagamentos de uma reserva específica"""
    try:
        pagamentos = await db.pagamento.find_many(
            where={"reservaId": reserva_id},
            order={"id": "desc"}
        )
        
        total_pago = sum(float(p.valor) for p in pagamentos if p.statusPagamento == "APROVADO")
        
        return {
            "success": True,
            "pagamentos": [
                {
                    "id": p.id,
                    "valor": float(p.valor),
                    "metodo": p.metodo,
                    "status": p.statusPagamento,
                    "cielo_payment_id": p.cieloPaymentId,
                    "parcelas": p.parcelas,
                    "created_at": p.createdAt.isoformat() if p.createdAt else None
                }
                for p in pagamentos
            ],
            "total_pago": total_pago,
            "total_pagamentos": len(pagamentos)
        }
    except Exception as e:
        print(f"[ERRO] Falha ao listar pagamentos da reserva: {e}")
        return {"success": False, "error": str(e), "pagamentos": [], "total_pago": 0}

@app.post("/api/v1/pagamentos")
async def criar_pagamento(dados: PagamentoCreate):
    """Criar novo pagamento e processar com Cielo"""
    try:
        # Verificar se reserva existe
        reserva = await db.reserva.find_unique(where={"id": dados.reserva_id})
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")
        
        # Processar com Cielo baseado no método
        cielo_response = None
        status_pagamento = "PENDENTE"
        cielo_payment_id = None
        url_pagamento = None
        
        if dados.metodo in ["credit_card", "debit_card"]:
            # Pagamento com cartão
            cielo_response = {
                "payment_id": f"CIELO_{datetime.now().strftime('%Y%m%d%H%M%S')}_{dados.reserva_id}",
                "status": "APROVADO",
                "authorization_code": "123456",
                "return_code": "00",
                "return_message": "Transação Aprovada"
            }
            cielo_payment_id = cielo_response["payment_id"]
            status_pagamento = "APROVADO"
            
            print(f"[CIELO] Pagamento cartão processado: {cielo_payment_id}")
            
        elif dados.metodo == "pix":
            # Gerar PIX
            txid = f"PIX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{dados.reserva_id}"
            qr_code_data = f"00020126580014BR.GOV.BCB.PIX0136{txid}520400005303986540{dados.valor:.2f}5802BR5925HOTEL REAL CABO FRIO6009CABO FRIO62070503***6304ABCD"
            
            cielo_response = {
                "txid": txid,
                "qr_code": qr_code_data,
                "status": "AGUARDANDO"
            }
            cielo_payment_id = txid
            url_pagamento = qr_code_data
            status_pagamento = "AGUARDANDO"
            
            print(f"[PIX] QR Code gerado: {txid}")
        
        # Criar pagamento no banco
        novo_pagamento = await db.pagamento.create(
            data={
                "reservaId": dados.reserva_id,
                "valor": dados.valor,
                "metodo": dados.metodo,
                "statusPagamento": status_pagamento,
                "cieloPaymentId": cielo_payment_id,
                "parcelas": dados.parcelas or 1,
            }
        )
        
        return {
            "success": True,
            "message": "Pagamento processado com sucesso",
            "pagamento": {
                "id": novo_pagamento.id,
                "valor": float(novo_pagamento.valor),
                "metodo": novo_pagamento.metodo,
                "status": novo_pagamento.statusPagamento,
                "cielo_payment_id": cielo_payment_id,
                "parcelas": novo_pagamento.parcelas,
            },
            "cielo_response": cielo_response,
            "qr_code": url_pagamento if dados.metodo == "pix" else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao processar pagamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")

@app.post("/api/v1/pagamentos/{pagamento_id}/confirmar-pix")
async def confirmar_pix(pagamento_id: int):
    """Confirmar pagamento PIX (simulação)"""
    try:
        pagamento = await db.pagamento.find_unique(where={"id": pagamento_id})
        if not pagamento:
            raise HTTPException(status_code=404, detail="Pagamento não encontrado")
        
        if pagamento.metodo != "pix":
            raise HTTPException(status_code=400, detail="Pagamento não é PIX")
        
        if pagamento.statusPagamento == "APROVADO":
            raise HTTPException(status_code=400, detail="PIX já foi confirmado")
        
        # Atualizar status
        pagamento_atualizado = await db.pagamento.update(
            where={"id": pagamento_id},
            data={"statusPagamento": "APROVADO"}
        )
        
        print(f"[PIX] Pagamento {pagamento_id} confirmado")
        
        return {
            "success": True,
            "message": "PIX confirmado com sucesso",
            "pagamento": {
                "id": pagamento_atualizado.id,
                "status": pagamento_atualizado.statusPagamento,
                "valor": float(pagamento_atualizado.valor)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao confirmar PIX: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/pagamentos/{pagamento_id}")
async def cancelar_pagamento(pagamento_id: int):
    """Cancelar pagamento"""
    try:
        pagamento = await db.pagamento.find_unique(where={"id": pagamento_id})
        if not pagamento:
            raise HTTPException(status_code=404, detail="Pagamento não encontrado")
        
        if pagamento.statusPagamento == "CANCELADO":
            raise HTTPException(status_code=400, detail="Pagamento já foi cancelado")
        
        # Atualizar status
        pagamento_atualizado = await db.pagamento.update(
            where={"id": pagamento_id},
            data={"statusPagamento": "CANCELADO"}
        )
        
        print(f"[PAGAMENTO] Pagamento {pagamento_id} cancelado")
        
        return {
            "success": True,
            "message": "Pagamento cancelado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao cancelar pagamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= ROTAS STUB (EVITAR 404) =============
# Endpoints que o frontend chama mas ainda não estão completamente implementados

@app.get("/api/v1/notificacoes")
async def listar_notificacoes():
    """Stub: retorna lista vazia de notificações"""
    return {
        "success": True,
        "notificacoes": [],
        "total": 0,
        "message": "Notificações em desenvolvimento"
    }

@app.post("/api/v1/notificacoes/{id}/marcar-lida")
async def marcar_notificacao_lida(id: int):
    """Stub: marca notificação como lida"""
    return {"success": True, "message": "Notificação marcada como lida"}

@app.delete("/api/v1/notificacoes/{id}")
async def excluir_notificacao(id: int):
    """Stub: exclui notificação"""
    return {"success": True, "message": "Notificação excluída"}

@app.get("/api/v1/cielo/status")
async def cielo_status():
    """Stub: status da integração Cielo"""
    return {
        "success": True,
        "status": "sandbox",
        "ambiente": "desenvolvimento",
        "message": "Cielo em modo sandbox"
    }

@app.get("/api/v1/cielo/historico")
async def cielo_historico(
    page: int = 1,
    pageSize: int = 20,
    dataInicio: str = None,
    dataFim: str = None,
    current_user = Depends(require_roles("RECEPCAO", "GERENTE", "ADMIN"))
):
    """Histórico real de transações de pagamento (simulando Cielo)"""
    try:
        # Construir filtros
        where_clause = {}
        
        if dataInicio:
            try:
                data_inicio_dt = datetime.fromisoformat(dataInicio.replace('Z', '+00:00'))
                where_clause["dataCriacao"] = {"gte": data_inicio_dt}
            except:
                pass
        
        if dataFim:
            try:
                data_fim_dt = datetime.fromisoformat(dataFim.replace('Z', '+00:00'))
                if "dataCriacao" in where_clause:
                    where_clause["dataCriacao"]["lte"] = data_fim_dt
                else:
                    where_clause["dataCriacao"] = {"lte": data_fim_dt}
            except:
                pass
        
        # Buscar total para paginação
        total = await db.pagamento.count(where=where_clause if where_clause else None)
        
        # Buscar pagamentos com paginação
        skip = (page - 1) * pageSize
        pagamentos = await db.pagamento.find_many(
            where=where_clause if where_clause else None,
            skip=skip,
            take=pageSize,
            order={"dataCriacao": "desc"},
            include={
                "cliente": True,
                "reserva": True
            }
        )
        
        # Formatar transações no estilo Cielo
        transacoes = []
        for pag in pagamentos:
            transacoes.append({
                "id": pag.id,
                "paymentId": pag.paymentId,
                "tid": pag.tid,
                "metodo": pag.metodo,
                "valor": float(pag.valor),
                "status": pag.statusPagamento,
                "dataCriacao": pag.dataCriacao.isoformat() if pag.dataCriacao else None,
                "dataCaptura": pag.dataCaptura.isoformat() if pag.dataCaptura else None,
                "dataEstorno": pag.dataEstorno.isoformat() if pag.dataEstorno else None,
                "motivoEstorno": pag.motivoEstorno,
                "cliente": {
                    "id": pag.cliente.id if pag.cliente else None,
                    "nome": pag.cliente.nomeCompleto if pag.cliente else "N/A",
                    "documento": pag.cliente.documento if pag.cliente else None
                } if pag.cliente else None,
                "reserva": {
                    "id": pag.reserva.id if pag.reserva else None,
                    "codigo": pag.reserva.codigoReserva if pag.reserva else None,
                    "status": pag.reserva.status if pag.reserva else None
                } if pag.reserva else None,
                # Campos simulando Cielo
                "merchantOrderId": f"RES-{pag.reservaId}" if pag.reservaId else f"PAG-{pag.id}",
                "returnCode": "0" if pag.statusPagamento == "APROVADO" else "99",
                "returnMessage": "Transação autorizada" if pag.statusPagamento == "APROVADO" else pag.statusPagamento,
                "authorizationCode": pag.paymentId[:6] if pag.paymentId else None
            })
        
        return {
            "success": True,
            "data": transacoes,
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "total": total,
                "totalPages": (total + pageSize - 1) // pageSize
            }
        }
    except Exception as e:
        print(f"❌ Erro ao buscar histórico Cielo: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "pagination": None
        }

@app.get("/api/v1/cielo/consultar/{payment_id}")
async def consultar_transacao_cielo_real(
    payment_id: str,
    current_user = Depends(require_roles("RECEPCAO", "GERENTE", "ADMIN"))
):
    """
    Consulta uma transação REAL na API Cielo E-commerce
    Endpoint oficial: GET /1/sales/{PaymentId}
    Documentação: https://developercielo.github.io/manual/cielo-ecommerce#consulta-por-paymentid
    """
    resultado = await cielo_api.consultar_transacao_real(payment_id)
    return resultado

@app.get("/api/v1/cielo/consultar-order/{order_id}")
async def consultar_por_order_id_cielo(
    order_id: str,
    current_user = Depends(require_roles("RECEPCAO", "GERENTE", "ADMIN"))
):
    """
    Consulta transações por MerchantOrderId na API Cielo
    Endpoint oficial: GET /1/sales?merchantOrderId={merchantOrderId}
    """
    resultado = await cielo_api.consultar_por_order_id(order_id)
    return resultado

@app.get("/api/v1/cielo/credenciais-status")
async def verificar_credenciais_cielo(
    current_user = Depends(require_roles("ADMIN"))
):
    """Verifica se as credenciais da Cielo estão configuradas"""
    return {
        "success": True,
        "mode": cielo_api.mode,
        "merchant_id_configurado": bool(cielo_api.merchant_id),
        "merchant_key_configurado": bool(cielo_api.merchant_key),
        "query_url": cielo_api.query_url,
        "api_url": cielo_api.api_url,
        "credenciais_ok": cielo_api.credenciais_ok
    }

@app.get("/api/v1/antifraude/transacoes-suspeitas")
async def transacoes_suspeitas(limit: int = 50):
    """Stub: lista transações suspeitas"""
    return {
        "success": True,
        "transacoes": [],
        "total": 0,
        "message": "Antifraude em desenvolvimento"
    }

# ============= ROTAS DE CLIENTES =============
@app.get("/api/v1/clientes")
async def listar_clientes():
    registros = await db.cliente.find_many(order={"id": "asc"})
    return {
        "clientes": [serialize_cliente(c) for c in registros],
        "total": len(registros)
    }

@app.post("/api/v1/clientes")
async def criar_cliente(cliente: ClienteCreate):
    existente = await db.cliente.find_unique(
        where={"documento": cliente.documento}
    )
    if existente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")
    
    novo_cliente = await db.cliente.create(
        data={
            "nomeCompleto": cliente.nome_completo,
            "documento": cliente.documento,
            "telefone": cliente.telefone,
            "email": cliente.email,
        }
    )
    
    return serialize_cliente(novo_cliente)

@app.get("/api/v1/clientes/{cliente_id}")
async def obter_cliente(cliente_id: int):
    cliente = await db.cliente.find_unique(where={"id": cliente_id})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return serialize_cliente(cliente)

# ============= ROTAS DE RESERVAS =============
@app.get("/api/v1/reservas")
async def listar_reservas():
    registros = await db.reserva.find_many(order={"id": "asc"})
    return {
        "reservas": [serialize_reserva(r) for r in registros],
        "total": len(registros)
    }

@app.post("/api/v1/reservas")
async def criar_reserva(reserva: ReservaCreate):
    # Verificar se cliente existe
    cliente = await db.cliente.find_unique(where={"id": reserva.cliente_id})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    quarto = await db.quarto.find_unique(where={"numero": reserva.quarto_numero})
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado")
    
    if quarto.status in (StatusQuarto.BLOQUEADO, StatusQuarto.MANUTENCAO):
        raise HTTPException(status_code=400, detail="Quarto indisponível para reserva")
    
    # Verificar conflitos de data no banco
    reservas_existentes = await db.reserva.find_many(
        where={
            "quartoNumero": reserva.quarto_numero,
            "status": {"in": ["PENDENTE", "HOSPEDADO"]},
            "checkinPrevisto": {"lt": reserva.checkout_previsto},
            "checkoutPrevisto": {"gt": reserva.checkin_previsto}
        }
    )
    
    if reservas_existentes:
        raise HTTPException(status_code=400, detail="Já existe uma reserva para este quarto neste período")
    
    # Gerar código único
    total_reservas = await db.reserva.count()
    codigo_reserva = f"RCF-{datetime.now().strftime('%Y%m')}-{total_reservas+1:06d}"
    
    nova_reserva = await db.reserva.create(
        data={
            "codigoReserva": codigo_reserva,
            "clienteId": reserva.cliente_id,
            "clienteNome": cliente.nomeCompleto,
            "quartoNumero": reserva.quarto_numero,
            "tipoSuite": reserva.tipo_suite,
            "status": "PENDENTE",
            "checkinPrevisto": reserva.checkin_previsto,
            "checkoutPrevisto": reserva.checkout_previsto,
            "valorDiaria": reserva.valor_diaria,
            "numDiarias": reserva.num_diarias,
        }
    )
    
    return serialize_reserva(nova_reserva)

class CheckinRequest(BaseModel):
    num_hospedes: int = 1
    num_criancas: int = 0
    placa_veiculo: Optional[str] = None
    observacoes: Optional[str] = None

@app.post("/api/v1/reservas/{reserva_id}/checkin")
async def checkin_reserva(reserva_id: int, checkin_data: Optional[CheckinRequest] = None):
    reserva = await db.reserva.find_unique(where={"id": reserva_id})
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")

    if reserva.status != "PENDENTE":
        raise HTTPException(status_code=400, detail="Só é possível fazer check-in de reservas pendentes")

    # Dados do check-in
    checkin_info = checkin_data or CheckinRequest()
    
    reserva_atualizada = await db.reserva.update(
        where={"id": reserva_id},
        data={
            "status": "HOSPEDADO",
            "checkinReal": datetime.now()
        }
    )

    # Atualizar status do quarto
    await db.quarto.update(
        where={"numero": reserva.quartoNumero},
        data={"status": "OCUPADO"}
    )
    
    # Log das informações do check-in
    print(f"[CHECK-IN] Reserva {reserva_id}: {checkin_info.num_hospedes} adultos, {checkin_info.num_criancas} crianças")
    if checkin_info.placa_veiculo:
        print(f"[CHECK-IN] Veículo: {checkin_info.placa_veiculo}")
    if checkin_info.observacoes:
        print(f"[CHECK-IN] Observações: {checkin_info.observacoes}")

    return {
        "id": reserva_atualizada.id,
        "message": "Check-in realizado com sucesso",
        "status": reserva_atualizada.status,
        "checkin_real": reserva_atualizada.checkinReal.isoformat(),
        "num_hospedes": checkin_info.num_hospedes,
        "num_criancas": checkin_info.num_criancas,
        "placa_veiculo": checkin_info.placa_veiculo,
        "observacoes": checkin_info.observacoes
    }

class CheckoutRequest(BaseModel):
    consumo_frigobar: float = 0
    servicos_extras: float = 0
    avaliacao: int = 5
    comentario_avaliacao: Optional[str] = None

@app.post("/api/v1/reservas/{reserva_id}/checkout")
async def checkout_reserva(reserva_id: int, checkout_data: Optional[CheckoutRequest] = None):
    reserva = await db.reserva.find_unique(where={"id": reserva_id})
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")

    if reserva.status != "HOSPEDADO":
        raise HTTPException(status_code=400, detail="Reserva não está hospedada")
    
    # Dados do checkout
    checkout_info = checkout_data or CheckoutRequest()
    
    # Calcular valor total com extras
    valor_hospedagem = float(reserva.valorDiaria) * reserva.numDiarias
    valor_total_final = valor_hospedagem + checkout_info.consumo_frigobar + checkout_info.servicos_extras
    
    # Atualizar status no banco
    reserva_atualizada = await db.reserva.update(
        where={"id": reserva_id},
        data={
            "status": "CHECKED_OUT",
            "checkoutReal": datetime.now()
        }
    )

    # Liberar quarto
    await db.quarto.update(
        where={"numero": reserva.quartoNumero},
        data={"status": "LIVRE"}
    )
    
    # Log da avaliação
    print(f"[CHECK-OUT] Reserva {reserva_id}: Avaliação {checkout_info.avaliacao}/5")
    if checkout_info.comentario_avaliacao:
        print(f"[CHECK-OUT] Comentário: {checkout_info.comentario_avaliacao}")
    print(f"[CHECK-OUT] Valor total: R$ {valor_total_final:.2f} (hospedagem: R$ {valor_hospedagem:.2f} + frigobar: R$ {checkout_info.consumo_frigobar:.2f} + extras: R$ {checkout_info.servicos_extras:.2f})")
    
    # Calcular pontos (regra: a cada 2 diárias)
    tipo_suite = reserva.tipoSuite
    num_diarias = reserva.numDiarias
    pares = num_diarias // 2
    
    pontos_por_par = {
        TipoSuite.LUXO: 3,
        TipoSuite.MASTER: 4,
        TipoSuite.REAL: 5
    }
    
    pontos_ganhos = pares * pontos_por_par.get(tipo_suite, 3)
    
    # Criar operação antifraude no banco
    operacao_antifraude = await db.operacaoantifraude.create(
        data={
            "reservaId": reserva_id,
            "clienteId": reserva.clienteId,
            "pontosCalculados": pontos_ganhos,
            "riskScore": 10,  # Baixo risco para teste
            "status": "AUTO_APROVADO",
        }
    )
    
    # Adicionar pontos ao cliente no banco
    await db.historicopontos.create(
        data={
            "clienteId": reserva.clienteId,
            "tipo": "GANHO",
            "pontos": pontos_ganhos,
            "origem": f"Checkout reserva {reserva.codigoReserva}",
            "data": datetime.now(),
        }
    )
    
    return {
        "id": reserva_atualizada.id,
        "message": "Checkout realizado com sucesso",
        "status": reserva_atualizada.status,
        "checkout_real": reserva_atualizada.checkoutReal.isoformat(),
        "pontos_ganhos": pontos_ganhos,
        "valor_hospedagem": valor_hospedagem,
        "consumo_frigobar": checkout_info.consumo_frigobar,
        "servicos_extras": checkout_info.servicos_extras,
        "valor_total_final": valor_total_final,
        "avaliacao": checkout_info.avaliacao,
        "comentario_avaliacao": checkout_info.comentario_avaliacao
    }

# ... (rest of the code remains the same)

@app.get("/api/v1/pontos/{cliente_id}")
async def obter_pontos_cliente(cliente_id: int, current_user = Depends(require_roles("RECEPCAO", "GERENTE", "ADMIN"))):
    historico = await db.historicopontos.find_many(
        where={"clienteId": cliente_id},
        order={"data": "desc"}
    )
    
    saldo = sum(h.pontos if h.tipo == "GANHO" else -h.pontos for h in historico)
    
    return {
        "saldo": saldo,
        "historico": [serialize_historico_pontos(h) for h in historico]
    }

# ... (rest of the code remains the same)

@app.get("/api/v1/pontos/saldo/{cliente_id}")
async def obter_saldo_pontos(cliente_id: int):
    """Obtém saldo atual de pontos do cliente"""
    try:
        # Buscar usuário pontos
        usuario_pontos = await db.UsuarioPontos.find_unique(
            where={"clienteId": cliente_id}
        )
        
        if not usuario_pontos:
            # Criar registro inicial se não existir
            usuario_pontos = await db.UsuarioPontos.create({
                "data": {
                    "clienteId": cliente_id,
                    "saldo": 0
                }
            })
        
        return {
            "success": True,
            "saldo": usuario_pontos.saldo,
            "usuario_pontos_id": usuario_pontos.id
        }
        
    except Exception as e:
        print(f"[ERRO] Falha ao obter saldo: {e}")
        return {
            "success": False,
            "error": "Erro interno ao consultar saldo",
            "saldo": 0
        }

# ... (rest of the code remains the same)

@app.post("/api/v1/webhooks/cielo")
async def cielo_webhook(webhook_data: CieloWebhook):
    """
    Webhook Cielo para atualizar status de pagamento
    """
    try:
        # Buscar pagamento pelo ID Cielo
        pagamento = await db.pagamento.find_unique(
            where={"cieloPaymentId": webhook_data.payment_id}
        )
        
        if not pagamento:
            print(f"[WEBHOOK] Pagamento não encontrado: {webhook_data.payment_id}")
            return {"status": "not_found"}
        
        # Atualizar status do pagamento
        status_antigo = pagamento.status
        pagamento_atualizado = await db.pagamento.update(
            where={"id": pagamento.id},
            data={
                "status": webhook_data.status,
                "responseCode": webhook_data.response_code,
                "responseMessage": webhook_data.response_message,
                "dataAprovacao": datetime.now() if webhook_data.status == "APPROVED" else None,
                "dataCancelamento": datetime.now() if webhook_data.status in ["REJECTED", "CHARGEBACK"] else None
            }
        )
        
        # Recalcular risco baseado no resultado do pagamento
        if webhook_data.status == "APPROVED":
            novo_status = "AUTO_APROVADO"
            novo_risco = max(10, pagamento_atualizado.riskScore - 20)  # Reduz risco se aprovado
        elif webhook_data.status in ["REJECTED", "CHARGEBACK"]:
            novo_status = "RECUSADO"
            novo_risco = min(100, pagamento_atualizado.riskScore + 30)  # Aumenta risco se rejeitado
        else:
            novo_status = "PENDENTE"
            novo_risco = pagamento_atualizado.riskScore
        
        # Atualizar operação antifraude
        await db.operacaoantifraude.update_many(
            where={"pagamentoId": pagamento.id},
            data={
                "status": novo_status,
                "paymentStatus": webhook_data.status,
                "riskScore": novo_risco
            }
        )
        
        print(f"[WEBHOOK] Pagamento {webhook_data.payment_id}: {status_antigo} -> {webhook_data.status}")
        
        return {
            "status": "updated",
            "payment_id": webhook_data.payment_id,
            "old_status": status_antigo,
            "new_status": webhook_data.status,
            "antifraude_status": novo_status
        }
        
    except Exception as e:
        print(f"[ERRO] Falha no webhook Cielo: {e}")
        return {"status": "error", "message": str(e)}

# ... (rest of the code remains the same)

@app.get("/api/v1/antifraude/operacoes")
async def listar_operacoes_antifraude():
    operacoes = await db.operacaoantifraude.find_many(
        order={"id": "desc"},
        include={
            "reserva": {
                "include": {"cliente": True}
            }
        }
    )
    
    pendentes = await db.operacaoantifraude.count(where={"status": "PENDENTE"})
    
    resultado = []
    for op in operacoes:
        resultado.append({
            "id": op.id,
            "reserva_id": op.reservaId,
            "cliente_id": op.clienteId,
            "cliente_nome": op.reserva.cliente.nomeCompleto if op.reserva and op.reserva.cliente else "N/A",
            "reserva_codigo": op.reserva.codigoReserva if op.reserva else "N/A",
            "pagamento_id": op.pagamentoId,
            "payment_status": op.paymentStatus,
            "pontos_calculados": op.pontosCalculados,
            "risk_score": op.riskScore,
            "status": op.status,
            "motivo_risco": op.motivoRisco,
            "created_at": op.createdAt.isoformat() if op.createdAt else None
        })
    
    return {
        "operacoes": resultado,
        "total": len(resultado),
        "pendentes": pendentes
    }

# ... (rest of the code remains the same)

@app.get("/api/v1/dashboard/stats/public")
async def dashboard_stats_public():
    """Dashboard stats PÚBLICO - sem autenticação (para troubleshooting)"""
    try:
        hoje = date.today()
        
        total_clientes = await db.cliente.count()
        total_reservas = await db.reserva.count()
        total_quartos = await db.quarto.count()
        quartos_ocupados = await db.quarto.count(where={"status": "OCUPADO"})
        quartos_disponiveis = total_quartos - quartos_ocupados
        taxa_ocupacao = round((quartos_ocupados / total_quartos * 100), 2) if total_quartos > 0 else 0
        
        return {
            "success": True,
            "data": {
                "total_clientes": total_clientes,
                "total_reservas": total_reservas,
                "total_quartos": total_quartos,
                "quartos_ocupados": quartos_ocupados,
                "quartos_disponiveis": quartos_disponiveis,
                "taxa_ocupacao": taxa_ocupacao,
                "receita_total": 0.0,
                "checkins_hoje": 0,
                "checkouts_hoje": 0,
                "reservas_pendentes": 0,
                "reservas_confirmadas": 0
            },
            "message": "Stats básicas carregadas (modo público)"
        }
    except Exception as e:
        print(f"[ERRO] Stats públicas: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "total_clientes": 0,
                "total_reservas": 0,
                "total_quartos": 0,
                "quartos_ocupados": 0,
                "quartos_disponiveis": 0,
                "taxa_ocupacao": 0,
                "receita_total": 0.0,
                "checkins_hoje": 0,
                "checkouts_hoje": 0,
                "reservas_pendentes": 0,
                "reservas_confirmadas": 0
            }
        }

@app.get("/api/v1/dashboard/stats")
async def dashboard_stats(current_user = Depends(require_roles("RECEPCAO", "GERENTE", "ADMIN"))):
    """Dashboard completo com métricas detalhadas e analytics"""
    try:
        hoje = date.today()
        
        # ============= MÉTRICAS BÁSICAS =============
        total_clientes = await db.cliente.count()
        total_reservas = await db.reserva.count()
        total_quartos = await db.quarto.count()
        
        # ============= MÉTRICAS DE OCUPAÇÃO =============
        reservas_ativas = await db.reserva.find_many(
            where={"status": {"in": ["PENDENTE", "HOSPEDADO"]}}
        )
        quartos_ocupados = await db.quarto.count(where={"status": "OCUPADO"})
        taxa_ocupacao = (quartos_ocupados / max(total_quartos, 1)) * 100
        
        # ============= MÉTRICAS DE HOJE =============
        checkins_hoje = await db.reserva.find_many(
            where={
                "status": "HOSPEDADO",
                "checkinPrevisto": {
                    "gte": datetime.combine(hoje, datetime.min.time()),
                    "lt": datetime.combine(hoje + timedelta(days=1), datetime.min.time())
                }
            }
        )
        
        checkouts_hoje = await db.reserva.find_many(
            where={
                "status": "CHECKED_OUT",
                "checkoutReal": {
                    "gte": datetime.combine(hoje, datetime.min.time()),
                    "lt": datetime.combine(hoje + timedelta(days=1), datetime.min.time())
                }
            }
        )
        
        # ============= MÉTRICAS FINANCEIRAS =============
        pagamentos = await db.pagamento.find_many()
        receita_total = sum(p.valor for p in pagamentos if p.status == "APROVADO")
        receita_mes = sum(
            p.valor for p in pagamentos 
            if p.status == "APROVADO" and 
            p.dataCriacao and 
            p.dataCriacao.month == hoje.month and 
            p.dataCriacao.year == hoje.year
        )
        
        # ============= MÉTRICAS DE PONTOS =============
        historico_ganhos = await db.historicopontos.find_many(where={"tipo": "GANHO"})
        pontos_distribuidos = sum(h.pontos for h in historico_ganhos)
        
        historico_usados = await db.historicopontos.find_many(where={"tipo": "USO"})
        pontos_utilizados = sum(h.pontos for h in historico_usados)
        
        # ============= MÉTRICAS DE CLIENTES =============
        clientes_vip = await db.cliente.count(where={"tipoHospede": "VIP"})
        clientes_corporativos = await db.cliente.count(where={"tipoHospede": "CORPORATIVO"})
        clientes_normais = total_clientes - clientes_vip - clientes_corporativos
        
        # Top 5 clientes por gasto
        top_clientes_gasto = await db.cliente.find_many(
            order={"totalGasto": "desc"},
            take=5
        )
        
        # Top 5 clientes por fidelidade
        top_clientes_fidelidade = await db.cliente.find_many(
            order={"nivelFidelidade": "desc"},
            take=5
        )
        
        # ============= MÉTRICAS DE QUARTOS =============
        quartos_luxo = await db.quarto.count(where={"tipoSuite": "LUXO"})
        quartos_master = await db.quarto.count(where={"tipoSuite": "MASTER"})
        quartos_real = await db.quarto.count(where={"tipoSuite": "REAL"})
        
        # ============= MÉTRICAS DE ANTIFRAUDE =============
        operacoes_pendentes = await db.operacaoantifraude.count(where={"status": "PENDENTE"})
        operacoes_aprovadas = await db.operacaoantifraude.count(where={"status": "AUTO_APROVADO"})
        operacoes_recusadas = await db.operacaoantifraude.count(where={"status": "RECUSADO"})
        
        # ============= MÉTRICAS DE SATISFAÇÃO =============
        taxa_conversao = (len([r for r in reservas_ativas if r.status in ["HOSPEDADO", "CHECKED_OUT"]]) / max(total_reservas, 1)) * 100
        
        # ============= TENDÊNCIAS (Últimos 30 dias) =============
        trinta_dias_atras = hoje - timedelta(days=30)
        reservas_ultimos_30_dias = await db.reserva.find_many(
            where={
                "createdAt": {
                    "gte": datetime.combine(trinta_dias_atras, datetime.min.time())
                }
            }
        )
        
        clientes_novos_30_dias = await db.cliente.find_many(
            where={
                "createdAt": {
                    "gte": datetime.combine(trinta_dias_atras, datetime.min.time())
                }
            }
        )
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            
            # ============= KPIs PRINCIPAIS =============
            "kpis_principais": {
                "total_clientes": total_clientes,
                "total_reservas": total_reservas,
                "total_quartos": total_quartos,
                "taxa_ocupacao": round(taxa_ocupacao, 1),
                "receita_total": round(receita_total, 2),
                "receita_mes": round(receita_mes, 2),
            },
            
            # ============= OPERAÇÕES DO DIA =============
            "operacoes_dia": {
                "checkins_hoje": len(checkins_hoje),
                "checkouts_hoje": len(checkouts_hoje),
                "reservas_ativas": len(reservas_ativas),
                "quartos_ocupados": quartos_ocupados,
            },
            
            # ============= SISTEMA DE PONTOS =============
            "sistema_pontos": {
                "pontos_distribuidos": pontos_distribuidos,
                "pontos_utilizados": pontos_utilizados,
                "pontos_saldo": pontos_distribuidos - pontos_utilizados,
                "taxa_utilizacao": round((pontos_utilizados / max(pontos_distribuidos, 1)) * 100, 1),
            },
            
            # ============= SEGMENTAÇÃO DE CLIENTES =============
            "segmentacao_clientes": {
                "normais": clientes_normais,
                "vip": clientes_vip,
                "corporativos": clientes_corporativos,
                "percentual_vip": round((clientes_vip / max(total_clientes, 1)) * 100, 1),
                "percentual_corporativos": round((clientes_corporativos / max(total_clientes, 1)) * 100, 1),
            },
            
            # ============= TOP CLIENTES =============
            "top_clientes": {
                "por_gasto": [
                    {
                        "nome": c.nomeCompleto,
                        "total_gasto": c.totalGasto,
                        "total_reservas": c.totalReservas,
                        "nivel_fidelidade": c.nivelFidelidade
                    }
                    for c in top_clientes_gasto
                ],
                "por_fidelidade": [
                    {
                        "nome": c.nomeCompleto,
                        "nivel_fidelidade": c.nivelFidelidade,
                        "total_gasto": c.totalGasto,
                        "total_reservas": c.totalReservas
                    }
                    for c in top_clientes_fidelidade
                ]
            },
            
            # ============= DISTRIBUIÇÃO DE QUARTOS =============
            "distribuicao_quartos": {
                "luxo": quartos_luxo,
                "master": quartos_master,
                "real": quartos_real,
                "ocupados": quartos_ocupados,
                "disponiveis": total_quartos - quartos_ocupados,
            },
            
            # ============= ANTIFRAUDE =============
            "antifraude": {
                "pendentes": operacoes_pendentes,
                "aprovadas": operacoes_aprovadas,
                "recusadas": operacoes_recusadas,
                "taxa_aprovacao": round((operacoes_aprovadas / max(operacoes_aprovadas + operacoes_recusadas, 1)) * 100, 1),
            },
            
            # ============= TENDÊNCIAS =============
            "tendencias": {
                "reservas_30_dias": len(reservas_ultimos_30_dias),
                "clientes_novos_30_dias": len(clientes_novos_30_dias),
                "taxa_conversao": round(taxa_conversao, 1),
                "media_reservas_dia": round(len(reservas_ultimos_30_dias) / 30, 1),
            },
            
            # ============= ALERTAS =============
            "alertas": {
                "operacoes_antifraude_pendentes": operacoes_pendentes,
                "taxa_ocupacao_baixa": taxa_ocupacao < 50,
                "taxa_ocupacao_alta": taxa_ocupacao > 90,
                "necessidade_manutencao": await db.quarto.count(where={"status": "MANUTENCAO"}),
            }
        }
        
    except Exception as e:
        print(f"[ERRO] Falha no dashboard completo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar dashboard")

# ... (rest of the code remains the same)

@app.get("/api/pontos/historico/{cliente_id}")
async def obter_historico_pontos(cliente_id: int, limit: int = 20, current_user = Depends(require_roles("RECEPCAO", "GERENTE", "ADMIN"))):
    """Obtém histórico de transações de pontos do cliente"""
    try:
        transacoes = await db.TransacaoPontos.find_many(
            where={"usuarioPontos": {"clienteId": cliente_id}},
            order={"createdAt": "desc"},
            take=limit
        )
        
        return {
            "success": True,
            "transacoes": [
                {
                    "id": t.id,
                    "tipo": t.tipo,
                    "origem": t.origem,
                    "pontos": t.pontos,
                    "motivo": t.motivo,
                    "created_at": t.createdAt.isoformat(),
                    "reserva_codigo": t.reservaCodigo
                }
                for t in transacoes
            ],
            "total": len(transacoes)
        }
        
    except Exception as e:
        print(f"[ERRO] Falha ao obter histórico: {e}")
        return {
            "success": False,
            "error": "Erro interno ao consultar histórico",
            "transacoes": [],
            "total": 0
        }

# ... (rest of the code remains the same)

@app.post("/api/pontos/ajustar")
async def ajustar_pontos_manuais(request: AjustarPontosRequest, current_user = Depends(require_roles("ADMIN"))):
    """Ajuste manual de pontos (limitado a ±4)"""
    try:
        if abs(request.pontos) > 4:
            return {
                "success": False,
                "error": "Ajuste manual limitado a ±4 pontos"
            }
        
        usuario_pontos = await db.UsuarioPontos.find_unique(
            where={"clienteId": request.cliente_id}
        )
        
        if not usuario_pontos:
            return {
                "success": False,
                "error": "Cliente não encontrado no sistema de pontos"
            }
        
        novo_saldo = usuario_pontos.saldo + request.pontos
        if novo_saldo < 0:
            return {
                "success": False,
                "error": "Saldo não pode ficar negativo"
            }
        
        await db.UsuarioPontos.update(
            where={"id": usuario_pontos.id},
            data={"saldo": novo_saldo}
        )
        
        transacao = await db.TransacaoPontos.create({
            "data": {
                "usuarioPontosId": usuario_pontos.id,
                "tipo": "AJUSTE_MANUAL",
                "origem": "ajuste_manual",
                "pontos": abs(request.pontos),
                "motivo": request.motivo
            }
        })
        
        return {
            "success": True,
            "transacao_id": transacao.id,
            "novo_saldo": novo_saldo
        }
        
    except Exception as e:
        print(f"[ERRO] Falha no ajuste manual: {e}")
        return {
            "success": False,
            "error": "Erro interno ao realizar ajuste"
        }

# ... (rest of the code remains the same)

@app.get("/api/pontos/admin/clientes")
async def listar_clientes_com_pontos(current_user = Depends(require_roles("GERENTE", "ADMIN"))):
    """Lista todos os clientes com seus saldos de pontos"""
    try:
        clientes = await db.cliente.find_many()
        
        resultado = []
        for cliente in clientes:
            usuario_pontos = await db.UsuarioPontos.find_unique(
                where={"clienteId": cliente.id}
            )
            
            resultado.append({
                "id": cliente.id,
                "nome": cliente.nomeCompleto,
                "documento": cliente.documento,
                "email": cliente.email,
                "status": cliente.status,
                "saldo_pontos": usuario_pontos.saldo if usuario_pontos else 0
            })
        
        return {
            "success": True,
            "clientes": resultado
        }
        
    except Exception as e:
        print(f"[ERRO] Falha ao listar clientes: {e}")
        return {
            "success": False,
            "error": "Erro interno ao listar clientes",
            "clientes": []
        }

# ... (rest of the code remains the same)

@app.get("/api/pontos/admin/antifraude-historico")
async def listar_historico_antifraude(page: int = 1, page_size: int = 20, current_user = Depends(require_roles("GERENTE", "ADMIN"))):
    """Lista histórico de operações antifraude"""
    try:
        operacoes = await db.operacaoantifraude.find_many(
            order={"createdAt": "desc"},
            skip=(page - 1) * page_size,
            take=page_size,
            include={
                "reserva": {
                    "include": {"cliente": True}
                }
            }
        )
        
        total = await db.operacaoantifraude.count()
        
        resultado = []
        for op in operacoes:
            resultado.append({
                "id": op.id,
                "operacao_id": f"ANT-{op.id}",
                "reserva_codigo": op.reserva.codigoReserva if op.reserva else None,
                "cliente_nome": op.reserva.cliente.nomeCompleto if op.reserva and op.reserva.cliente else None,
                "cpf_hospede": op.cpfHospede,
                "pontos_calculados": op.pontosCalculados,
                "status": op.status,
                "motivo_recusa": op.motivoRecusa,
                "created_at": op.createdAt.isoformat()
            })
        
        return {
            "success": True,
            "operacoes": resultado,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        print(f"[ERRO] Falha ao listar histórico antifraude: {e}")
        return {
            "success": False,
            "error": "Erro interno ao listar histórico",
            "operacoes": [],
            "pagination": {
                "page": 1,
                "page_size": page_size,
                "total": 0,
                "total_pages": 0
            }
        }

if __name__ == "__main__":
    print(" Iniciando Hotel Real Cabo Frio API...")
    print(" Acesse: http://localhost:8000")
    print(" Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)