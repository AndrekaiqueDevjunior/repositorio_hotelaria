from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request, status
from app.schemas.reserva_schema import ReservaCreate, ReservaResponse
from app.services.reserva_service import ReservaService
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.core.database import get_db
from app.utils.export_utils import export_to_csv, export_to_pdf_simple
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.middleware.idempotency import check_idempotency, store_idempotency_result
from app.core.cache import redis_lock
from app.core.validators import ReservaValidator, QuartoValidator
from typing import Optional
from starlette.responses import JSONResponse
from datetime import datetime
import base64
import binascii
import os

router = APIRouter(prefix="/reservas", tags=["reservas"])

# Dependency injection
async def get_reserva_service() -> ReservaService:
    db = get_db()
    return ReservaService(
        ReservaRepository(db),
        ClienteRepository(db),
        QuartoRepository(db)
    )

@router.get("", response_model=dict)
async def listar_reservas(
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(get_current_active_user),
    search: Optional[str] = Query(None, description="Busca por nome cliente ou número quarto"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    checkin_inicio: Optional[str] = Query(None, description="Data checkin início (YYYY-MM-DD)"),
    checkin_fim: Optional[str] = Query(None, description="Data checkin fim (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Limite de resultados"),
    offset: Optional[int] = Query(0, description="Offset para paginação")
):
    """Listar todas as reservas - Requer autenticação"""
    return await service.list_all(
        search=search,
        status=status,
        checkin_inicio=checkin_inicio,
        checkin_fim=checkin_fim,
        limit=limit,
        offset=offset
    )

@router.get("/ultimas", response_model=dict)
async def listar_ultimas_reservas(
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(get_current_active_user),
    status_filter: Optional[str] = Query("CONFIRMADA,CHECKIN,EM_ANDAMENTO", description="Status das reservas a serem filtradas, separados por vírgula", alias="status"),
    limit: int = Query(5, description="Número máximo de reservas a retornar", ge=1, le=20)
):
    """
    Listar as últimas reservas ativas - Requer autenticação
    
    Retorna as últimas reservas com status ativo (CONFIRMADA, CHECKIN, EM_ANDAMENTO)
    """
    try:
        # Converter a string de status em uma lista
        status_list = [s.strip() for s in status_filter.split(",")] if status_filter else []
        
        # Obter as reservas - usar createdAt em vez de data_criacao
        result = await service.list_all(
            status=",".join(status_list),
            limit=limit,
            order_by="createdAt:desc"
        )
        
        return {
            "success": True,
            "data": result.get("data", [])
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar últimas reservas: {str(e)}"
        )

@router.post("", status_code=201)
async def criar_reserva(
    reserva: ReservaCreate,
    request: Request,
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(get_current_active_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Criar nova reserva com proteção de idempotência
    
    Headers:
        Idempotency-Key: UUID único (opcional mas recomendado)
    
    Retorna:
        201 Created com dados da reserva
    """
    
    # CAMADA 1: Validar dados de entrada
    checkin_date = reserva.checkin_previsto if isinstance(reserva.checkin_previsto, datetime) else datetime.strptime(str(reserva.checkin_previsto), "%Y-%m-%d")
    checkout_date = reserva.checkout_previsto if isinstance(reserva.checkout_previsto, datetime) else datetime.strptime(str(reserva.checkout_previsto), "%Y-%m-%d")
    
    ReservaValidator.validar_datas(
        checkin_date.date() if isinstance(checkin_date, datetime) else checkin_date,
        checkout_date.date() if isinstance(checkout_date, datetime) else checkout_date
    )
    
    # CAMADA 2: Verificar idempotência
    if idempotency_key:
        cached = await check_idempotency(idempotency_key)
        if cached:
            return JSONResponse(
                content=cached["body"],
                status_code=cached["status_code"]
            )
    
    # CAMADA 3: Lock para evitar race condition
    lock_key = f"quarto:{reserva.quarto_numero}:{reserva.checkin_previsto}"
    
    try:
        async with redis_lock(lock_key, timeout=10):
            # CAMADA 4: Validar disponibilidade do quarto
            db = get_db()
            await QuartoValidator.validar_disponibilidade(
                reserva.quarto_numero,
                checkin_date.date() if isinstance(checkin_date, datetime) else checkin_date,
                checkout_date.date() if isinstance(checkout_date, datetime) else checkout_date,
                db
            )
            
            # CAMADA 5: Criar reserva
            nova_reserva = await service.create(reserva)
            
            result = {
                "success": True,
                "data": nova_reserva,
                "message": "Reserva criada com sucesso"
            }
            
            # Cachear resultado
            if idempotency_key:
                await store_idempotency_result(idempotency_key, result, status_code=201)
            
            return JSONResponse(content=result, status_code=201)
            
    except TimeoutError:
        raise HTTPException(
            status_code=409,
            detail="Outro processo está criando reserva para este quarto. Tente novamente."
        )

@router.get("/{reserva_id}", response_model=ReservaResponse)
async def obter_reserva(
    reserva_id: int,
    service: ReservaService = Depends(get_reserva_service)
):
    """Obter reserva por ID"""
    return await service.get_by_id(reserva_id)

# Rotas legadas mantidas para compatibilidade (deprecated)
@router.post("/{reserva_id}/checkin", response_model=ReservaResponse, deprecated=True)
async def checkin_reserva_legacy(
    reserva_id: int,
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(get_current_active_user)
):
    """[DEPRECATED] Use POST /api/v1/checkin/{reserva_id}/realizar"""
    raise HTTPException(
        status_code=410,
        detail="Endpoint descontinuado. Use /api/v1/checkin/{reserva_id}/realizar"
    )

@router.post("/{reserva_id}/checkout", response_model=ReservaResponse, deprecated=True)
async def checkout_reserva_legacy(
    reserva_id: int,
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(get_current_active_user)
):
    """[DEPRECATED] Use POST /api/v1/checkin/{reserva_id}/checkout/realizar"""
    raise HTTPException(
        status_code=410,
        detail="Endpoint descontinuado. Use /api/v1/checkin/{reserva_id}/checkout/realizar"
    )

@router.get("/cliente/{cliente_id}", response_model=list)
async def listar_reservas_cliente(
    cliente_id: int,
    service: ReservaService = Depends(get_reserva_service)
):
    """Listar reservas de um cliente"""
    return await service.list_by_cliente(cliente_id)

# Rotas legadas mantidas para compatibilidade (deprecated)
@router.patch("/{reserva_id}/cancelar", response_model=ReservaResponse, deprecated=True)
async def cancelar_reserva_legacy(
    reserva_id: int,
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """[DEPRECATED] Use PATCH /{reserva_id} com status='CANCELADO'"""
    return await service.cancelar(reserva_id)

@router.post("/{reserva_id}/confirmar", response_model=ReservaResponse, deprecated=True)
async def confirmar_reserva_legacy(
    reserva_id: int,
    service: ReservaService = Depends(get_reserva_service)
):
    """[DEPRECATED] Use PATCH /{reserva_id} com status='CONFIRMADO'"""
    return await service.confirmar(reserva_id)

@router.put("/{reserva_id}", response_model=ReservaResponse)
async def atualizar_reserva(
    reserva_id: int,
    reserva_data: dict,
    service: ReservaService = Depends(get_reserva_service)
):
    """Atualizar dados gerais da reserva"""
    return await service.update(reserva_id, reserva_data)

@router.patch("/{reserva_id}", response_model=ReservaResponse)
async def atualizar_reserva_parcial(
    reserva_id: int,
    reserva_data: dict,
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Atualizar reserva parcialmente (REST-compliant)
    
    Exemplos de uso:
    - Check-in: PATCH /{id} com {"status": "CHECKED_IN"}
    - Check-out: PATCH /{id} com {"status": "CHECKED_OUT"}
    - Cancelar: PATCH /{id} com {"status": "CANCELADO"}
    - Confirmar: PATCH /{id} com {"status": "CONFIRMADO"}
    """
    # Detectar ações especiais baseadas no status
    if "status" in reserva_data:
        status = reserva_data["status"]
        if status in ("CHECKED_IN", "CHECKED_OUT"):
            raise HTTPException(
                status_code=410,
                detail="Transições de check-in/check-out via PATCH descontinuadas. Use /api/v1/checkin/*"
            )
        elif status == "CANCELADO":
            return await service.cancelar(reserva_id)
        elif status == "CONFIRMADO":
            return await service.confirmar(reserva_id)
    
    # Atualização parcial normal
    return await service.update(reserva_id, reserva_data)

from pydantic import BaseModel

class ComprovanteUploadRequest(BaseModel):
    arquivo_base64: str
    nome_arquivo: str
    metodo_pagamento: str
    observacao: Optional[str] = None

@router.post("/{reserva_id}/comprovante", status_code=201)
async def upload_comprovante_reserva(
    reserva_id: int,
    dados: ComprovanteUploadRequest,
    service: ReservaService = Depends(get_reserva_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload de comprovante de pagamento para reserva
    
    Fluxo:
    1. Cliente escolhe "Pagamento no balcão" no modal
    2. Sistema muda status para AGUARDANDO_COMPROVANTE
    3. Cliente faz upload do comprovante (este endpoint)
    4. Sistema muda status para EM_ANALISE
    5. Admin aprova/rejeita em /comprovantes
    
    Body:
    {
        "arquivo_base64": "base64_string",
        "nome_arquivo": "comprovante.jpg",
        "metodo_pagamento": "PIX|DINHEIRO|DEBITO|CREDITO",
        "observacao": "Pago no débito"
    }
    """
    from app.repositories.comprovante_repo import ComprovanteRepository
    from app.schemas.comprovante_schema import ComprovanteUpload, TipoComprovante

    try:
        db = get_db()

        # 0. Validar formato do arquivo por extensão (alinhado com o frontend)
        nome_arquivo = (dados.nome_arquivo or "").strip()
        ext = os.path.splitext(nome_arquivo.lower())[1]
        allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".pdf", ".heic", ".heif"}
        if ext not in allowed_exts:
            raise ValueError(
                "Formato de arquivo não suportado. Use JPG, PNG, WEBP, HEIC/HEIF ou PDF."
            )

        # Validar base64 e tamanho (máx 5MB)
        try:
            arquivo_bytes = base64.b64decode(dados.arquivo_base64, validate=True)
        except (binascii.Error, ValueError) as e:
            raise ValueError(f"Arquivo base64 inválido: {str(e)}")

        if len(arquivo_bytes) > 5 * 1024 * 1024:
            raise ValueError("Arquivo muito grande. Tamanho máximo: 5MB")

        # 1. Validar que a reserva existe e está no status correto
        reserva = await db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva não encontrada")

        if reserva.statusReserva not in ["PENDENTE_PAGAMENTO", "AGUARDANDO_COMPROVANTE", "PENDENTE"]:
            raise HTTPException(
                status_code=400,
                detail=f"Reserva não está aguardando pagamento (status atual: {reserva.statusReserva})"
            )

        # 2. Criar ou buscar pagamento associado à reserva
        pagamento = await db.pagamento.find_first(
            where={"reservaId": reserva_id}
        )

        if not pagamento:
            # Criar pagamento pendente
            pagamento = await db.pagamento.create(
                data={
                    "metodo": dados.metodo_pagamento,
                    "valor": float(reserva.valorDiaria) * reserva.numDiarias,
                    "statusPagamento": "PENDENTE",
                    "cliente": {"connect": {"id": reserva.clienteId}},
                    "reserva": {"connect": {"id": reserva_id}},
                }
            )

        # 3. Upload do comprovante
        comprovante_repo = ComprovanteRepository(db)

        # Mapear método de pagamento para tipo de comprovante
        tipo_map = {
            "PIX": TipoComprovante.PIX,
            "TRANSFERENCIA": TipoComprovante.TRANSFERENCIA,
            "DINHEIRO": TipoComprovante.DINHEIRO,
            "DEBITO": TipoComprovante.CARTAO,
            "CREDITO": TipoComprovante.CARTAO,
        }
        tipo_comprovante = tipo_map.get(dados.metodo_pagamento.upper(), TipoComprovante.OUTRO)

        comprovante_data = ComprovanteUpload(
            pagamento_id=pagamento.id,
            tipo_comprovante=tipo_comprovante,
            arquivo_base64=dados.arquivo_base64,
            nome_arquivo=dados.nome_arquivo,
            observacoes=dados.observacao,
            valor_confirmado=float(reserva.valorDiaria) * reserva.numDiarias
        )

        result = await comprovante_repo.upload_comprovante(comprovante_data)

        # 4. Atualizar status da reserva para EM_ANALISE
        await db.reserva.update(
            where={"id": reserva_id},
            data={"statusReserva": "EM_ANALISE"}
        )

        return {
            "success": True,
            "message": "Comprovante enviado com sucesso! Aguardando análise do administrador.",
            "reserva_id": reserva_id,
            "pagamento_id": pagamento.id,
            "comprovante": result.get("comprovante"),
            "status_reserva": "EM_ANALISE"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao enviar comprovante: {str(e)}")

@router.get("/export/csv")
async def exportar_reservas_csv(
    service: ReservaService = Depends(get_reserva_service),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    checkin_inicio: Optional[str] = Query(None),
    checkin_fim: Optional[str] = Query(None)
):
    """Exportar reservas para CSV"""
    result = await service.list_all(
        search=search, 
        status=status, 
        checkin_inicio=checkin_inicio,
        checkin_fim=checkin_fim,
        limit=10000, 
        offset=0
    )
    return export_to_csv(result["reservas"], "reservas.csv")

@router.get("/export/pdf")
async def exportar_reservas_pdf(
    service: ReservaService = Depends(get_reserva_service),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    checkin_inicio: Optional[str] = Query(None),
    checkin_fim: Optional[str] = Query(None)
):
    """Exportar reservas para PDF"""
    result = await service.list_all(
        search=search, 
        status=status, 
        checkin_inicio=checkin_inicio,
        checkin_fim=checkin_fim,
        limit=10000, 
        offset=0
    )
    return export_to_pdf_simple(result["reservas"], "reservas.pdf", "Relatório de Reservas")