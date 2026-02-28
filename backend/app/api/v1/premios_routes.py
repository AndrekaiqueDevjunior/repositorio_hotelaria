"""
Rotas para o sistema de prêmios/recompensas.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from app.schemas.premio_schema import (
    PremioCreate, PremioUpdate, PremioResponse,
    ResgatePremioRequest, ResgatePremioResponse,
    ResgateHistoricoResponse, ConfirmarEntregaRequest,
    PremiosDisponiveis, ResgatePremioPublicoRequest
)
from app.repositories.premio_repo import PremioRepository
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic
from app.repositories.pontos_repo import PontosRepository
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.middleware.rate_limit import rate_limit_moderate, rate_limit_strict
import os
import httpx

router = APIRouter(prefix="/premios", tags=["premios"])


async def _validar_recaptcha_publico(request: Request, action_esperada: str) -> None:
    secret = (os.getenv("RECAPTCHA_SECRET_KEY") or "").strip()
    if not secret:
        return

    token = (request.headers.get("X-Recaptcha-Token") or "").strip()
    action = (request.headers.get("X-Recaptcha-Action") or "").strip()

    if not token:
        raise HTTPException(status_code=403, detail="Antifraude: validação obrigatória")

    if action_esperada and action and action != action_esperada:
        raise HTTPException(status_code=403, detail="Antifraude: ação inválida")

    min_score_raw = (os.getenv("RECAPTCHA_MIN_SCORE") or "0.5").strip()
    try:
        min_score = float(min_score_raw)
    except Exception:
        min_score = 0.5

    data = {
        "secret": secret,
        "response": token,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        payload = resp.json() if resp.content else {}

    if not payload.get("success"):
        raise HTTPException(status_code=403, detail="Antifraude: validação falhou")

    if action_esperada:
        payload_action = payload.get("action")
        if payload_action and payload_action != action_esperada:
            raise HTTPException(status_code=403, detail="Antifraude: ação inválida")

    score = payload.get("score")
    if score is not None:
        try:
            score_f = float(score)
        except Exception:
            score_f = 0.0
        if score_f < min_score:
            raise HTTPException(status_code=403, detail="Antifraude: baixa confiança")


async def get_premio_repo() -> PremioRepository:
    db = get_db()
    return PremioRepository(db)


@router.get("", response_model=List[PremioResponse])
async def listar_premios(
    apenas_ativos: bool = True,
    repo: PremioRepository = Depends(get_premio_repo)
):
    """
    Listar todos os prêmios disponíveis.
    
    - **apenas_ativos**: Se True, retorna apenas prêmios ativos (padrão: True)
    
    Não requer autenticação para consulta pública.
    """
    return await repo.list_all(apenas_ativos=apenas_ativos)


@router.get("/disponiveis/{cliente_id}", response_model=PremiosDisponiveis)
async def listar_premios_disponiveis_cliente(
    cliente_id: int,
    repo: PremioRepository = Depends(get_premio_repo),
    current_user: User = Depends(get_current_active_user)
):
    """
    Listar prêmios disponíveis para um cliente específico.
    
    Retorna:
    - Saldo atual de pontos
    - Prêmios que o cliente pode resgatar
    - Prêmios próximos (que faltam poucos pontos)
    """
    db = get_db()
    pontos_repo = PontosRepository(db)
    
    # Obter saldo do cliente
    saldo_data = await pontos_repo.get_saldo(cliente_id)
    saldo_atual = saldo_data.get("saldo", 0)
    
    # Obter todos os prêmios ativos
    premios = await repo.list_all(apenas_ativos=True)
    
    # Separar prêmios disponíveis e próximos
    disponiveis = []
    proximos = []
    
    for premio in premios:
        custo = premio["preco_em_pontos"]
        if saldo_atual >= custo:
            disponiveis.append(premio)
        elif saldo_atual >= custo * 0.7:  # Falta menos de 30%
            proximos.append({
                **premio,
                "pontos_faltantes": custo - saldo_atual
            })
    
    return {
        "cliente_id": cliente_id,
        "saldo_atual": saldo_atual,
        "premios_disponiveis": disponiveis,
        "premios_proximos": proximos
    }


@router.get("/{premio_id}", response_model=PremioResponse)
async def obter_premio(
    premio_id: int,
    repo: PremioRepository = Depends(get_premio_repo)
):
    """Obter detalhes de um prêmio específico"""
    premio = await repo.get_by_id(premio_id)
    if not premio:
        raise HTTPException(status_code=404, detail="Prêmio não encontrado")
    return premio


@router.post("", response_model=PremioResponse, status_code=201)
async def criar_premio(
    premio: PremioCreate,
    repo: PremioRepository = Depends(get_premio_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Criar novo prêmio.
    
    Requer: ADMIN ou GERENTE
    """
    return await repo.create(premio.model_dump())


@router.put("/{premio_id}", response_model=PremioResponse)
async def atualizar_premio(
    premio_id: int,
    premio: PremioUpdate,
    repo: PremioRepository = Depends(get_premio_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Atualizar prêmio existente.
    
    Requer: ADMIN ou GERENTE
    """
    resultado = await repo.update(premio_id, premio.model_dump(exclude_unset=True))
    if not resultado:
        raise HTTPException(status_code=404, detail="Prêmio não encontrado")
    return resultado


@router.post("/resgatar-publico", response_model=dict)
async def resgatar_premio_publico(
    request: ResgatePremioPublicoRequest,
    http_request: Request,
    _rate_limit: None = Depends(rate_limit_strict)
):
    """
    Resgate público de prêmio (sem autenticação).
    
    **TRANSAÇÃO ATÔMICA:** Previne race conditions no resgate
    """
    try:
        from app.repositories.cliente_repo import ClienteRepository
        from app.repositories.pontos_repo import PontosRepository

        db = get_db()
        cliente_repo = ClienteRepository(db)
        pontos_repo = PontosRepository(db)

        documento_limpo = ''.join(filter(str.isdigit, request.cliente_documento))
        if not documento_limpo or len(documento_limpo) not in [11, 14]:
            raise HTTPException(
                status_code=400,
                detail="CPF/CNPJ inválido. Deve conter 11 (CPF) ou 14 (CNPJ) dígitos."
            )

        cliente = await cliente_repo.get_by_documento(documento_limpo)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado. Verifique o CPF/CNPJ informado.")

        cliente_id = cliente['id']

        saldo_data = await pontos_repo.get_saldo(cliente_id)
        saldo_atual = saldo_data.get('saldo', 0)

        await _validar_recaptcha_publico(http_request, "resgatar_premio_publico")

        # USAR REPOSITÓRIO ATÔMICO (previne race conditions)
        repo = PremioRepositoryAtomic(db)

        resultado = await repo.resgatar_atomic(
            premio_id=request.premio_id,
            cliente_id=cliente_id,
            funcionario_id=None
        )

        if not resultado.get('success'):
            raise HTTPException(status_code=400, detail=resultado.get('error'))

        return {
            "success": True,
            "message": "Prêmio resgatado com sucesso!",
            "data": {
                "resgate_id": resultado.get("resgate_id"),
                "premio": resultado.get("premio"),
                "pontos_usados": resultado.get("pontos_usados"),
                "saldo_anterior": saldo_atual,
                "novo_saldo": resultado.get("novo_saldo"),
                "observacoes": request.observacoes,
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar resgate: {str(e)}")


@router.delete("/{premio_id}", status_code=204)
async def deletar_premio(
    premio_id: int,
    repo: PremioRepository = Depends(get_premio_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Desativar prêmio (soft delete).
    
    Requer: ADMIN ou GERENTE
    """
    resultado = await repo.delete(premio_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Prêmio não encontrado")
    return


@router.post("/resgatar", response_model=ResgatePremioResponse)
async def resgatar_premio(
    request: ResgatePremioRequest,
    current_user: User = Depends(get_current_active_user),
    _rate_limit: None = Depends(rate_limit_strict)
):
    """
    Resgatar prêmio usando pontos.
    
    Este endpoint:
    1. Verifica se o cliente tem saldo suficiente
    2. Debita os pontos do cliente
    3. Cria registro de resgate
    4. Atualiza estoque (se aplicável)
    
    **Rate limit**: 5 resgates por minuto
    **TRANSAÇÃO ATÔMICA:** Previne race conditions no resgate
    """
    # USAR REPOSITÓRIO ATÔMICO (previne race conditions)
    db = get_db()
    repo = PremioRepositoryAtomic(db)
    
    try:
        resultado = await repo.resgatar_atomic(
            premio_id=request.premio_id,
            cliente_id=request.cliente_id,
            funcionario_id=current_user.id if hasattr(current_user, 'id') else None
        )
        
        if not resultado.get("success"):
            raise HTTPException(status_code=400, detail=resultado.get("error"))
        
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar resgate: {str(e)}")


@router.get("/resgates/{cliente_id}", response_model=List[ResgateHistoricoResponse])
async def listar_resgates_cliente(
    cliente_id: int,
    repo: PremioRepository = Depends(get_premio_repo),
    current_user: User = Depends(get_current_active_user)
):
    """
    Listar histórico de resgates de um cliente.
    """
    return await repo.listar_resgates_cliente(cliente_id)


@router.post("/resgates/{resgate_id}/entregar", response_model=dict)
async def confirmar_entrega_premio(
    resgate_id: int,
    repo: PremioRepository = Depends(get_premio_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Confirmar entrega de prêmio resgatado.
    
    Requer: ADMIN ou GERENTE
    """
    resultado = await repo.confirmar_entrega(
        resgate_id=resgate_id,
        funcionario_id=current_user.id if hasattr(current_user, 'id') else None
    )
    
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    
    return resultado


@router.get("/consulta/{documento}", response_model=dict)
async def consultar_premios_por_documento(
    documento: str,
    request: Request,
    repo: PremioRepository = Depends(get_premio_repo),
    _rate_limit: None = Depends(rate_limit_moderate)
):
    """
    Consulta pública de prêmios disponíveis por CPF/CNPJ.
    
    Não requer autenticação.
    
    Retorna:
    - Nome do cliente
    - Saldo de pontos
    - Prêmios disponíveis para resgate
    - Histórico de resgates
    """
    await _validar_recaptcha_publico(request, "consultar_premios")

    from app.repositories.cliente_repo import ClienteRepository
    from app.repositories.pontos_repo import PontosRepository
    
    db = get_db()
    
    # Limpar documento
    documento_limpo = ''.join(filter(str.isdigit, documento))
    
    if not documento_limpo or len(documento_limpo) not in [11, 14]:
        raise HTTPException(
            status_code=400,
            detail="CPF/CNPJ inválido. Deve conter 11 (CPF) ou 14 (CNPJ) dígitos."
        )
    
    # Buscar cliente
    cliente_repo = ClienteRepository(db)
    cliente = await cliente_repo.get_by_documento(documento_limpo)
    
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado. Verifique o CPF/CNPJ informado."
        )
    
    cliente_id = cliente['id']
    
    # Obter saldo
    pontos_repo = PontosRepository(db)
    saldo_data = await pontos_repo.get_saldo(cliente_id)
    saldo_atual = saldo_data.get("saldo", 0)
    
    # Obter prêmios disponíveis
    premios = await repo.list_all(apenas_ativos=True)
    
    disponiveis = []
    proximos = []
    
    for premio in premios:
        custo = premio["preco_em_pontos"]
        if saldo_atual >= custo:
            disponiveis.append(premio)
        elif saldo_atual >= custo * 0.5:  # Falta menos de 50%
            proximos.append({
                **premio,
                "pontos_faltantes": custo - saldo_atual
            })
    
    # Obter histórico de resgates
    resgates = await repo.listar_resgates_cliente(cliente_id)
    
    return {
        "success": True,
        "cliente": {
            "nome": cliente.get('nome_completo', 'Cliente'),
            "documento": documento_limpo
        },
        "saldo_pontos": saldo_atual,
        "premios_disponiveis": disponiveis,
        "premios_proximos": proximos,
        "historico_resgates": resgates
    }
