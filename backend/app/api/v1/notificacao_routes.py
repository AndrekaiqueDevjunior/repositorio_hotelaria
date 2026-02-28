"""
Rotas de Notificações
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, User
from app.services.notification_service import NotificationService
from app.repositories.notificacao_repo import NotificacaoRepository
from pydantic import BaseModel

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])

class NotificacaoResponse(BaseModel):
    id: int
    titulo: str
    mensagem: str
    tipo: str
    categoria: str
    perfil: Optional[str]
    lida: bool
    reserva_id: Optional[int]
    pagamento_id: Optional[int]
    url_acao: Optional[str]
    created_at: str
    lida_at: Optional[str]

    class Config:
        from_attributes = True

class ContagemResponse(BaseModel):
    success: bool
    count: int

class ListaResponse(BaseModel):
    success: bool
    notificacoes: List[NotificacaoResponse]
    total: int
    total_nao_lidas: int

# Dependency injection
async def get_notification_service(db = Depends(get_db)) -> NotificationService:
    return NotificationService(db)

@router.get("/nao-lidas", response_model=ContagemResponse)
async def obter_notificacoes_nao_lidas(
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Obter contagem de notificações não lidas do usuário atual"""
    try:
        usuario_id = current_user.id
        perfil = current_user.perfil
        
        count = await service.contar_nao_lidas(usuario_id=usuario_id, perfil=perfil)
        
        return ContagemResponse(success=True, count=count)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter notificações: {str(e)}")

@router.get("", response_model=ListaResponse)
async def listar_notificacoes(
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tipo: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    apenas_nao_lidas: bool = Query(False)
):
    """Listar notificações do usuário"""
    try:
        usuario_id = current_user.id
        perfil = current_user.perfil
        
        # Obter notificações
        notificacoes = await service.listar_notificacoes_usuario(
            usuario_id=usuario_id,
            perfil=perfil,
            apenas_nao_lidas=apenas_nao_lidas,
            limit=limit,
            offset=offset
        )
        
        # Converter para response
        notificacoes_response = []
        for notif in notificacoes:
            # Aplicar filtros se especificados
            if tipo and notif.get("tipo") != tipo:
                continue
            if categoria and notif.get("categoria") != categoria:
                continue
                
            notificacoes_response.append(NotificacaoResponse(
                id=notif.get("id"),
                titulo=notif.get("titulo"),
                mensagem=notif.get("mensagem"),
                tipo=notif.get("tipo"),
                categoria=notif.get("categoria"),
                perfil=notif.get("perfil"),
                lida=notif.get("lida"),
                reserva_id=notif.get("reserva_id"),
                pagamento_id=notif.get("pagamento_id"),
                url_acao=notif.get("url_acao"),
                created_at=notif.get("created_at"),
                lida_at=notif.get("lida_at")
            ))
        
        # Contar totais
        total_nao_lidas = await service.contar_nao_lidas(usuario_id=usuario_id, perfil=perfil)
        
        return ListaResponse(
            success=True,
            notificacoes=notificacoes_response,
            total=len(notificacoes_response),
            total_nao_lidas=total_nao_lidas
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar notificações: {str(e)}")

@router.post("/{notificacao_id}/marcar-lida")
async def marcar_notificacao_como_lida(
    notificacao_id: int,
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Marcar notificação como lida"""
    try:
        success = await service.marcar_como_lida(notificacao_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
            
        return {"success": True, "message": "Notificação marcada como lida"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao marcar notificação: {str(e)}")

@router.post("/marcar-todas-lidas")
async def marcar_todas_como_lidas(
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Marcar todas as notificações como lidas"""
    try:
        usuario_id = current_user.id
        perfil = current_user.perfil
        
        count = await service.marcar_todas_lidas(usuario_id=usuario_id, perfil=perfil)
        
        return {
            "success": True, 
            "message": f"{count} notificações marcadas como lidas"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao marcar todas: {str(e)}")

@router.delete("/{notificacao_id}")
async def deletar_notificacao(
    notificacao_id: int,
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Deletar notificação específica"""
    try:
        repo = service.repo
        success = await repo.delete_by_id(notificacao_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
            
        return {"success": True, "message": "Notificação deletada"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar notificação: {str(e)}")

@router.delete("/limpar-antigas")
async def limpar_notificacoes_antigas(
    dias: int = Query(30, ge=1, le=365),
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """Limpar notificações lidas antigas"""
    try:
        # Apenas admin pode limpar
        if current_user.perfil != "ADMIN":
            raise HTTPException(status_code=403, detail="Apenas administradores podem limpar notificações")
        
        count = await service.limpar_antigas(dias=dias)
        
        return {
            "success": True,
            "message": f"{count} notificações antigas removidas"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar notificações: {str(e)}")
