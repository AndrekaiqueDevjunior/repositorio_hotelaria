"""
Rotas da API para Prêmios RP (Reais Pontos)
Gerencia o catálogo de prêmios e sistema de resgate
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.repositories.premios_rp_repo import PremiosRPRepository
from app.repositories.pontos_repo import PontosRepository
from app.repositories.cliente_repo import ClienteRepository
from app.core.database import get_db
from app.middleware.auth_middleware import require_admin_or_manager
from app.core.security import User
from app.middleware.rate_limit import rate_limit_moderate
from pydantic import BaseModel
from app.core.enums import CategoriaPremio
from app.utils.datetime_utils import now_utc

router = APIRouter(prefix="/premios-rp", tags=["premios-rp"])

# Schemas Pydantic
class PremioRPCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    categoria: CategoriaPremio
    preco_em_rp: int
    imagem_url: Optional[str] = None
    estoque: Optional[int] = 0
    valor_estimado: Optional[int] = None
    ativo: Optional[bool] = True

class PremioRPResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    categoria: CategoriaPremio
    preco_em_rp: int
    imagem_url: Optional[str]
    estoque: int
    valor_estimado: Optional[int]
    ativo: bool
    created_at: str

class ResgatePremioRequest(BaseModel):
    premio_id: int
    cliente_documento: str
    observacoes: Optional[str] = None

class ResgatePremioResponse(BaseModel):
    id: int
    premio_id: int
    cliente_id: int
    pontos_utilizados: int
    status_resgate: str
    data_solicitacao: str
    data_aprovacao: Optional[str]
    data_entrega: Optional[str]
    observacoes: Optional[str]

# Dependency injection
async def get_premios_repo() -> PremiosRPRepository:
    db = get_db()
    return PremiosRPRepository(db)

# Rotas Públicas (para clientes)
@router.get("/catalogo", response_model=List[PremioRPResponse])
async def listar_catalogo_premios(
    categoria: Optional[CategoriaPremio] = None,
    ativo: bool = True,
    repo: PremiosRPRepository = Depends(get_premios_repo),
    _rate_limit: None = Depends(rate_limit_moderate)
):
    """
    Listar catálogo de prêmios disponíveis para resgate (público)
    
    - **categoria**: Filtrar por categoria (DIARIA, ELETRONICO, etc.)
    - **ativo**: Apenas prêmios ativos (default: true)
    """
    premios = await repo.list_premios(ativo=ativo, categoria=categoria)
    
    return [
        PremioRPResponse(
            id=p.id,
            nome=p.nome,
            descricao=p.descricao,
            categoria=p.categoria,
            preco_em_rp=p.preco_em_rp,
            imagem_url=p.imagem_url,
            estoque=p.estoque,
            valor_estimado=p.valor_estimado,
            ativo=p.ativo,
            created_at=p.created_at.isoformat()
        )
        for p in premios
    ]

@router.post("/resgatar", response_model=dict)
async def resgatar_premio_publico(
    request: ResgatePremioRequest,
    repo: PremiosRPRepository = Depends(get_premios_repo),
    _rate_limit: None = Depends(rate_limit_moderate)
):
    """
    Resgatar prêmio usando pontos RP (público para clientes)
    
    - **premio_id**: ID do prêmio desejado
    - **cliente_documento**: CPF/CNPJ do cliente
    - **observacoes**: Observações opcionais
    
    **Processo:**
    1. Validar cliente pelo documento
    2. Verificar saldo de pontos RP
    3. Verificar disponibilidade do prêmio
    4. Criar solicitação de resgate
    5. Debitar pontos do cliente
    """
    try:
        # 1. Validar cliente
        db = get_db()
        cliente_repo = ClienteRepository(db)
        pontos_repo = PontosRepository(db)
        
        # Limpar documento (remover formatação)
        documento_limpo = ''.join(filter(str.isdigit, request.cliente_documento))
        
        cliente = await cliente_repo.get_by_documento(documento_limpo)
        if not cliente:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado. Verifique o CPF/CNPJ informado."
            )
        
        # 2. Verificar prêmio
        premio = await repo.get_premio_by_id(request.premio_id)
        if not premio or not premio.ativo:
            raise HTTPException(
                status_code=404,
                detail="Prêmio não encontrado ou indisponível."
            )
        
        if premio.estoque <= 0:
            raise HTTPException(
                status_code=400,
                detail="Prêmio sem estoque disponível."
            )
        
        # 3. Verificar saldo de pontos
        saldo_data = await pontos_repo.get_saldo_rp(cliente['id'])
        saldo_atual = saldo_data.get('saldo_rp', 0)
        
        if saldo_atual < premio.preco_em_rp:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente. Você tem {saldo_atual} RP, mas precisa de {premio.preco_em_rp} RP."
            )
        
        # 4. Criar resgate
        resgate_data = {
            "premio_id": request.premio_id,
            "cliente_id": cliente['id'],
            "pontos_utilizados": premio.preco_em_rp,
            "observacoes": request.observacoes
        }
        
        resgate = await repo.criar_resgate(resgate_data)
        
        # 5. Debitar pontos
        await pontos_repo.debitar_pontos_rp(
            cliente_id=cliente['id'],
            pontos=premio.preco_em_rp,
            motivo=f"Resgate do prêmio: {premio.nome}",
            origem="RESGATE_PREMIO",
            reserva_id=None
        )
        
        # 6. Atualizar estoque
        await repo.update_premio(premio.id, {"estoque": premio.estoque - 1})
        
        return {
            "success": True,
            "message": "Prêmio resgatado com sucesso!",
            "data": {
                "resgate_id": resgate.id,
                "premio_nome": premio.nome,
                "pontos_utilizados": premio.preco_em_rp,
                "status": "PENDENTE",
                "data_solicitacao": resgate.data_solicitacao.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar resgate: {str(e)}"
        )

# Rotas Administrativas
@router.get("", response_model=List[PremioRPResponse])
async def listar_premios_admin(
    ativo: Optional[bool] = None,
    categoria: Optional[CategoriaPremio] = None,
    repo: PremiosRPRepository = Depends(get_premios_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """Listar todos os prêmios (admin)"""
    premios = await repo.list_premios(ativo=ativo, categoria=categoria)
    
    return [
        PremioRPResponse(
            id=p.id,
            nome=p.nome,
            descricao=p.descricao,
            categoria=p.categoria,
            preco_em_rp=p.preco_em_rp,
            imagem_url=p.imagem_url,
            estoque=p.estoque,
            valor_estimado=p.valor_estimado,
            ativo=p.ativo,
            created_at=p.created_at.isoformat()
        )
        for p in premios
    ]

@router.post("", response_model=PremioRPResponse)
async def criar_premio(
    premio: PremioRPCreate,
    repo: PremiosRPRepository = Depends(get_premios_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """Criar novo prêmio (admin)"""
    premio_data = premio.dict()
    novo_premio = await repo.create_premio(premio_data)
    
    return PremioRPResponse(
        id=novo_premio.id,
        nome=novo_premio.nome,
        descricao=novo_premio.descricao,
        categoria=novo_premio.categoria,
        preco_em_rp=novo_premio.preco_em_rp,
        imagem_url=novo_premio.imagem_url,
        estoque=novo_premio.estoque,
        valor_estimado=novo_premio.valor_estimado,
        ativo=novo_premio.ativo,
        created_at=novo_premio.created_at.isoformat()
    )

@router.get("/resgates", response_model=List[ResgatePremioResponse])
async def listar_resgates_admin(
    status: Optional[str] = None,
    repo: PremiosRPRepository = Depends(get_premios_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """Listar todos os resgates (admin)"""
    resgates = await repo.list_resgates(status=status)
    
    return [
        ResgatePremioResponse(
            id=r.id,
            premio_id=r.premio_id,
            cliente_id=r.cliente_id,
            pontos_utilizados=r.pontos_utilizados,
            status_resgate=r.status_resgate,
            data_solicitacao=r.data_solicitacao.isoformat(),
            data_aprovacao=r.data_aprovacao.isoformat() if r.data_aprovacao else None,
            data_entrega=r.data_entrega.isoformat() if r.data_entrega else None,
            observacoes=r.observacoes
        )
        for r in resgates
    ]

@router.patch("/resgates/{resgate_id}/status")
async def atualizar_status_resgate(
    resgate_id: int,
    novo_status: str,
    repo: PremiosRPRepository = Depends(get_premios_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """Atualizar status de resgate (admin)"""
    resgate = await repo.atualizar_status_resgate(resgate_id, novo_status, current_user.get('id'))
    
    if not resgate:
        raise HTTPException(
            status_code=404,
            detail="Resgate não encontrado."
        )
    
    return {
        "success": True,
        "message": f"Status do resgate {resgate_id} atualizado para {novo_status}",
        "data": {
            "resgate_id": resgate.id,
            "status_atual": resgate.status_resgate,
            "data_atualizacao": now_utc().isoformat()
        }
    }

@router.get("/estatisticas")
async def obter_estatisticas_premios(
    repo: PremiosRPRepository = Depends(get_premios_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """Obter estatísticas dos prêmios (admin)"""
    return await repo.get_estatisticas_premios()
