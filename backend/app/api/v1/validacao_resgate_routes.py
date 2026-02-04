"""
Rotas para validação de resgates de prêmios
Sistema anti-fraude para verificar códigos de resgate
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
import logging

router = APIRouter(prefix="/validacao-resgates", tags=["validacao-resgates"])
security_logger = logging.getLogger("security")


class ValidarResgateRequest(BaseModel):
    codigo_resgate: str  # Formato: RES-000001


class ValidarResgateResponse(BaseModel):
    valido: bool
    resgate_id: Optional[int] = None
    cliente_nome: Optional[str] = None
    cliente_documento: Optional[str] = None
    premio_nome: Optional[str] = None
    pontos_usados: Optional[int] = None
    status: Optional[str] = None
    data_resgate: Optional[str] = None
    ja_entregue: bool = False
    funcionario_resgate: Optional[str] = None
    funcionario_entrega: Optional[str] = None
    mensagem: Optional[str] = None
    # 🆕 Campos para trajetória de pontos
    pontos_atuais: Optional[int] = None
    total_gasto: Optional[float] = None
    total_reservas: Optional[int] = None
    nivel_fidelidade: Optional[str] = None
    historico_pontos: Optional[list] = None
    resgates_anteriores: Optional[list] = None


class ConfirmarEntregaRequest(BaseModel):
    codigo_resgate: str


@router.post("/validar", response_model=ValidarResgateResponse)
async def validar_codigo_resgate(
    request: ValidarResgateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Validar código de resgate de prêmio.
    
    Verifica se o código é válido e retorna informações do resgate.
    
    **Segurança:**
    - Requer autenticação
    - Registra todas as tentativas de validação
    - Detecta códigos inválidos ou já utilizados
    """
    try:
        db = get_db()
        
        # Extrair ID do código (RES-000001 -> 1)
        codigo_limpo = request.codigo_resgate.replace("RES-", "").lstrip("0")
        
        if not codigo_limpo or not codigo_limpo.isdigit():
            security_logger.warning(
                f"Tentativa de validação com código inválido: {request.codigo_resgate} "
                f"por funcionário {current_user.id}"
            )
            return ValidarResgateResponse(
                valido=False,
                mensagem="❌ Código inválido. Formato esperado: RES-XXXXXX"
            )
        
        resgate_id = int(codigo_limpo)
        
        # Buscar resgate no banco com dados completos do cliente
        resgate = await db.resgatepremio.find_unique(
            where={"id": resgate_id},
            include={
                "cliente": {
                    "include": {
                        "usuarioPontos": {
                            "include": {
                                "transacoes": {
                                    "take": 10,
                                    "order": {"createdAt": "desc"}
                                }
                            }
                        },
                        "resgatePremios": {
                            "take": 5,
                            "order": {"createdAt": "desc"}
                        }
                    }
                },
                "premio": True,
                "funcionario": True,
                "funcionarioEntrega": True
            }
        )
        
        if not resgate:
            security_logger.warning(
                f"Tentativa de validação de código inexistente: {request.codigo_resgate} "
                f"por funcionário {current_user.id}"
            )
            return ValidarResgateResponse(
                valido=False,
                mensagem="❌ Código não encontrado no sistema. Verifique o código digitado."
            )
        
        # Verificar se já foi entregue
        ja_entregue = resgate.status == "ENTREGUE"
        
        # 🆕 Extrair dados da trajetória de pontos
        pontos_atuais = None
        total_gasto = None
        total_reservas = None
        nivel_fidelidade = None
        historico_pontos = []
        resgates_anteriores = []
        
        if resgate.cliente:
            # Dados básicos do cliente
            pontos_atuais = resgate.cliente.usuarioPontos.saldo if resgate.cliente.usuarioPontos else 0
            total_gasto = resgate.cliente.totalGasto
            total_reservas = resgate.cliente.totalReservas
            nivel_fidelidade = resgate.cliente.nivelFidelidade
            
            # Histórico de transações de pontos
            if resgate.cliente.usuarioPontos and resgate.cliente.usuarioPontos.transacoes:
                for transacao in resgate.cliente.usuarioPontos.transacoes:
                    historico_pontos.append({
                        "data": transacao.createdAt.isoformat() if transacao.createdAt else None,
                        "tipo": transacao.tipo,
                        "pontos": transacao.pontos,
                        "origem": transacao.origem,
                        "motivo": transacao.motivo,
                        "reserva_id": transacao.reservaId
                    })
            
            # Resgates anteriores
            if resgate.cliente.resgatePremios:
                for resgate_anterior in resgate.cliente.resgatePremios:
                    if resgate_anterior.id != resgate.id:  # Excluir o resgate atual
                        resgates_anteriores.append({
                            "id": resgate_anterior.id,
                            "codigo": f"RES-{str(resgate_anterior.id).zfill(6)}",
                            "premio": resgate_anterior.premio.nome if resgate_anterior.premio else "N/A",
                            "pontos_usados": resgate_anterior.pontosUsados,
                            "status": resgate_anterior.status,
                            "data": resgate_anterior.createdAt.isoformat() if resgate_anterior.createdAt else None
                        })
        
        if ja_entregue:
            security_logger.warning(
                f"Tentativa de validação de resgate já entregue: {request.codigo_resgate} "
                f"(ID: {resgate_id}) por funcionário {current_user.id}"
            )
        else:
            security_logger.info(
                f"Validação de resgate bem-sucedida: {request.codigo_resgate} "
                f"(ID: {resgate_id}) por funcionário {current_user.id}"
            )
        
        return ValidarResgateResponse(
            valido=True,
            resgate_id=resgate.id,
            cliente_nome=resgate.cliente.nomeCompleto if resgate.cliente else None,
            cliente_documento=resgate.cliente.documento if resgate.cliente else None,
            premio_nome=resgate.premio.nome if resgate.premio else None,
            pontos_usados=resgate.pontosUsados,
            status=resgate.status,
            data_resgate=resgate.createdAt.isoformat() if resgate.createdAt else None,
            ja_entregue=ja_entregue,
            funcionario_resgate=resgate.funcionario.nome if resgate.funcionario else "Sistema",
            funcionario_entrega=resgate.funcionarioEntrega.nome if resgate.funcionarioEntrega else None,
            mensagem="✅ Código válido!" if not ja_entregue else "⚠️ Este prêmio já foi entregue!",
            # 🆕 Dados da trajetória
            pontos_atuais=pontos_atuais,
            total_gasto=total_gasto,
            total_reservas=total_reservas,
            nivel_fidelidade=nivel_fidelidade,
            historico_pontos=historico_pontos,
            resgates_anteriores=resgates_anteriores
        )
        
    except Exception as e:
        security_logger.error(f"Erro ao validar resgate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao validar código: {str(e)}")


@router.post("/confirmar-entrega", response_model=dict)
async def confirmar_entrega_resgate(
    request: ConfirmarEntregaRequest,
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Confirmar entrega de prêmio resgatado.
    
    Marca o resgate como ENTREGUE e registra o funcionário responsável.
    
    **Segurança:**
    - Requer ADMIN ou GERENTE
    - Registra quem entregou e quando
    - Impede dupla entrega
    """
    try:
        db = get_db()
        
        # Extrair ID do código
        codigo_limpo = request.codigo_resgate.replace("RES-", "").lstrip("0")
        
        if not codigo_limpo or not codigo_limpo.isdigit():
            raise HTTPException(status_code=400, detail="Código inválido")
        
        resgate_id = int(codigo_limpo)
        
        # Buscar resgate
        resgate = await db.resgatepremio.find_unique(
            where={"id": resgate_id},
            include={"cliente": True, "premio": True}
        )
        
        if not resgate:
            raise HTTPException(status_code=404, detail="Resgate não encontrado")
        
        if resgate.status == "ENTREGUE":
            security_logger.warning(
                f"Tentativa de confirmar entrega duplicada: {request.codigo_resgate} "
                f"por funcionário {current_user.id}"
            )
            raise HTTPException(
                status_code=400,
                detail="Este prêmio já foi entregue anteriormente"
            )
        
        # Confirmar entrega
        await db.resgatepremio.update(
            where={"id": resgate_id},
            data={
                "status": "ENTREGUE",
                "funcionarioEntregaId": current_user.id
            }
        )
        
        security_logger.info(
            f"Entrega confirmada: {request.codigo_resgate} "
            f"(Cliente: {resgate.cliente.nomeCompleto if resgate.cliente else 'N/A'}, "
            f"Prêmio: {resgate.premio.nome if resgate.premio else 'N/A'}) "
            f"por funcionário {current_user.nome} (ID: {current_user.id})"
        )
        
        return {
            "success": True,
            "message": "✅ Entrega confirmada com sucesso!",
            "resgate_id": resgate_id,
            "cliente": resgate.cliente.nomeCompleto if resgate.cliente else None,
            "premio": resgate.premio.nome if resgate.premio else None,
            "funcionario_entrega": current_user.nome
        }
        
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Erro ao confirmar entrega: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao confirmar entrega: {str(e)}")


@router.get("/historico", response_model=dict)
async def listar_resgates_pendentes(
    status: str = "PENDENTE",
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """
    Listar resgates por status.
    
    **Status disponíveis:**
    - PENDENTE: Aguardando entrega
    - ENTREGUE: Já entregue ao cliente
    """
    try:
        db = get_db()
        
        resgates = await db.resgatepremio.find_many(
            where={"status": status},
            include={
                "cliente": True,
                "premio": True,
                "funcionario": True,
                "funcionarioEntrega": True
            },
            order={"createdAt": "desc"},
            take=limit
        )
        
        return {
            "success": True,
            "total": len(resgates),
            "status_filtro": status,
            "resgates": [
                {
                    "codigo": f"RES-{str(r.id).zfill(6)}",
                    "resgate_id": r.id,
                    "cliente_nome": r.cliente.nomeCompleto if r.cliente else None,
                    "cliente_documento": r.cliente.documento if r.cliente else None,
                    "premio_nome": r.premio.nome if r.premio else None,
                    "pontos_usados": r.pontosUsados,
                    "status": r.status,
                    "data_resgate": r.createdAt.isoformat() if r.createdAt else None,
                    "funcionario_resgate": r.funcionario.nome if r.funcionario else "Sistema",
                    "funcionario_entrega": r.funcionarioEntrega.nome if r.funcionarioEntrega else None
                }
                for r in resgates
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar resgates: {str(e)}")
