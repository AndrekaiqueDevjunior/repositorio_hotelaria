"""
Rotas para auditoria do sistema
Permite consultar quem fez o quê, quando e como
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
import logging

router = APIRouter(prefix="/auditoria", tags=["auditoria"])
audit_logger = logging.getLogger("audit")


def traduzir_acao(acao: str) -> str:
    """Traduz ações técnicas para linguagem amigável"""
    traducoes = {
        "CREATE": "Criou",
        "UPDATE": "Atualizou",
        "DELETE": "Excluiu",
        "LOGIN": "Fez login",
        "LOGOUT": "Fez logout",
        "CONFIRM": "Confirmou",
        "CREDITO": "Creditou pontos",
        "DEBITO": "Debitou pontos",
        "DELIVER": "Entregou prêmio",
        "ACCESS_DENIED": "Acesso negado",
    }
    
    for chave, valor in traducoes.items():
        if chave in acao.upper():
            return valor
    
    return acao


class AuditoriaResponse(BaseModel):
    id: int
    funcionario_id: int
    funcionario_nome: Optional[str] = None
    funcionario_email: Optional[str] = None
    funcionario_perfil: Optional[str] = None
    entidade: str
    entidade_id: str
    acao: str
    acao_descricao: Optional[str] = None
    payload_resumo: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: str
    detalhes: Optional[Dict[str, Any]] = None


class AuditoriaFiltros(BaseModel):
    funcionario_id: Optional[int] = None
    entidade: Optional[str] = None
    acao: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    ip_address: Optional[str] = None


class FuncionarioSimples(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str


@router.get("/funcionarios", response_model=List[FuncionarioSimples])
async def listar_funcionarios(
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Listar todos os funcionários para filtros.
    
    **Requer ADMIN ou GERENTE**
    """
    try:
        db = get_db()
        
        funcionarios = await db.funcionario.find_many(
            where={"status": "ATIVO"},
            order={"nome": "asc"}
        )
        
        return [
            FuncionarioSimples(
                id=f.id,
                nome=f.nome,
                email=f.email,
                perfil=f.perfil
            )
            for f in funcionarios
        ]
        
    except Exception as e:
        audit_logger.error(f"Erro ao listar funcionários: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar funcionários: {str(e)}")


@router.get("/logs", response_model=List[AuditoriaResponse])
async def listar_logs_auditoria(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(50, ge=1, le=100, description="Itens por página"),
    funcionario_id: Optional[int] = Query(None, description="ID do funcionário"),
    entidade: Optional[str] = Query(None, description="Tipo de entidade"),
    acao: Optional[str] = Query(None, description="Ação realizada"),
    data_inicio: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    ip_address: Optional[str] = Query(None, description="Endereço IP"),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Listar logs de auditoria com filtros avançados.
    
    **Requer ADMIN**
    
    Permite filtrar por:
    - Usuário específico
    - Tipo de entidade (reserva, pagamento, pontos, etc.)
    - Ação (CREATE, UPDATE, DELETE, etc.)
    - Período de tempo
    - Endereço IP
    """
    try:
        db = get_db()
        
        # Construir filtros
        where_clause = {}
        
        if funcionario_id:
            where_clause["funcionarioId"] = funcionario_id
        
        if entidade:
            where_clause["entidade"] = {"contains": entidade, "mode": "insensitive"}
        
        if acao:
            where_clause["acao"] = {"contains": acao, "mode": "insensitive"}
        
        if data_inicio or data_fim:
            created_at_filter = {}
            if data_inicio:
                try:
                    start_date = datetime.strptime(data_inicio, "%Y-%m-%d")
                    created_at_filter["gte"] = start_date
                except ValueError:
                    raise HTTPException(status_code=400, detail="Formato de data_inicio inválido. Use YYYY-MM-DD")
            
            if data_fim:
                try:
                    end_date = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
                    created_at_filter["lt"] = end_date
                except ValueError:
                    raise HTTPException(status_code=400, detail="Formato de data_fim inválido. Use YYYY-MM-DD")
            
            where_clause["createdAt"] = created_at_filter
        
        if ip_address:
            where_clause["ipAddress"] = {"contains": ip_address, "mode": "insensitive"}
        
        # Buscar logs com paginação
        skip = (page - 1) * limit
        
        logs = await db.auditoria.find_many(
            where=where_clause,
            include={
                "funcionario": True
            },
            order={"createdAt": "desc"},
            skip=skip,
            take=limit
        )
        
        # Contar total para paginação
        total = await db.auditoria.count(where=where_clause)
        
        # Formatar resposta
        resposta = []
        for log in logs:
            resposta.append(AuditoriaResponse(
                id=log.id,
                funcionario_id=log.funcionarioId,
                funcionario_nome=log.funcionario.nome if log.funcionario else "Sistema",
                funcionario_email=log.funcionario.email if log.funcionario else None,
                funcionario_perfil=log.funcionario.perfil if log.funcionario else None,
                entidade=log.entidade,
                entidade_id=log.entidadeId,
                acao=log.acao,
                acao_descricao=traduzir_acao(log.acao),
                payload_resumo=log.payloadResumo,
                ip_address=log.ipAddress,
                user_agent=log.userAgent,
                created_at=log.createdAt.isoformat(),
                detalhes={
                    "pagina": page,
                    "limite": limit,
                    "total": total,
                    "total_paginas": (total + limit - 1) // limit
                } if page == 1 else None  # Incluir detalhes apenas na primeira página
            ))
        
        audit_logger.info(
            f"Consulta de auditoria por admin {current_user.id}: "
            f"{len(resposta)} registros encontrados"
        )
        
        return resposta
        
    except Exception as e:
        audit_logger.error(f"Erro ao listar logs de auditoria: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar logs: {str(e)}")


@router.get("/resumo", response_model=Dict[str, Any])
async def resumo_auditoria(
    dias: int = Query(7, ge=1, le=90, description="Número de dias para análise"),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Obter resumo estatístico dos logs de auditoria.
    
    **Requer ADMIN**
    
    Retorna estatísticas como:
    - Total de ações por tipo
    - Usuários mais ativos
    - Entidades mais acessadas
    - Ações por hora do dia
    """
    try:
        db = get_db()
        
        # Calcular data de corte
        data_corte = datetime.now() - timedelta(days=dias)
        
        # Buscar logs do período
        logs = await db.auditoria.find_many(
            where={
                "createdAt": {"gte": data_corte}
            },
            include={
                "funcionario": True
            },
            take=10000  # Limite para performance
        )
        
        # Análise estatística
        resumo = {
            "periodo_analise": f"Últimos {dias} dias",
            "total_acoes": len(logs),
            "acoes_por_tipo": {},
            "usuarios_mais_ativos": {},
            "entidades_mais_acessadas": {},
            "acoes_por_hora": {},
            "top_ips": {}
        }
        
        for log in logs:
            # Ações por tipo
            acao = log.acao
            resumo["acoes_por_tipo"][acao] = resumo["acoes_por_tipo"].get(acao, 0) + 1
            
            # Usuários mais ativos
            if log.funcionario:
                funcionario_nome = log.funcionario.nome
                resumo["usuarios_mais_ativos"][funcionario_nome] = resumo["usuarios_mais_ativos"].get(funcionario_nome, 0) + 1
            
            # Entidades mais acessadas
            entidade = log.entidade
            resumo["entidades_mais_acessadas"][entidade] = resumo["entidades_mais_acessadas"].get(entidade, 0) + 1
            
            # Ações por hora
            hora = log.createdAt.hour if log.createdAt else 0
            resumo["acoes_por_hora"][str(hora)] = resumo["acoes_por_hora"].get(str(hora), 0) + 1
            
            # Top IPs
            if log.ipAddress:
                ip = log.ipAddress
                resumo["top_ips"][ip] = resumo["top_ips"].get(ip, 0) + 1
        
        # Ordenar resultados (top 10)
        resumo["acoes_por_tipo"] = dict(sorted(resumo["acoes_por_tipo"].items(), key=lambda x: x[1], reverse=True)[:10])
        resumo["usuarios_mais_ativos"] = dict(sorted(resumo["usuarios_mais_ativos"].items(), key=lambda x: x[1], reverse=True)[:10])
        resumo["entidades_mais_acessadas"] = dict(sorted(resumo["entidades_mais_acessadas"].items(), key=lambda x: x[1], reverse=True)[:10])
        resumo["top_ips"] = dict(sorted(resumo["top_ips"].items(), key=lambda x: x[1], reverse=True)[:10])
        
        audit_logger.info(
            f"Resumo de auditoria gerado por admin {current_user.id}: "
            f"{resumo['total_acoes']} ações analisadas"
        )
        
        return resumo
        
    except Exception as e:
        audit_logger.error(f"Erro ao gerar resumo de auditoria: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")


@router.get("/detalhes/{log_id}", response_model=AuditoriaResponse)
async def detalhes_log_auditoria(
    log_id: int,
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Obter detalhes completos de um log específico.
    
    **Requer ADMIN**
    """
    try:
        db = get_db()
        
        log = await db.auditoria.find_unique(
            where={"id": log_id},
            include={
                "funcionario": True
            }
        )
        
        if not log:
            raise HTTPException(status_code=404, detail="Log de auditoria não encontrado")
        
        audit_logger.info(
            f"Detalhes do log {log_id} consultados por admin {current_user.id}"
        )
        
        return AuditoriaResponse(
            id=log.id,
            funcionario_id=log.funcionarioId,
            funcionario_nome=log.funcionario.nome if log.funcionario else None,
            entidade=log.entidade,
            entidade_id=log.entidadeId,
            acao=log.acao,
            payload_resumo=log.payloadResumo,
            ip_address=log.ipAddress,
            user_agent=log.userAgent,
            created_at=log.createdAt.isoformat(),
            detalhes={
                "funcionario_email": log.funcionario.email if log.funcionario else None,
                "funcionario_perfil": log.funcionario.perfil if log.funcionario else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        audit_logger.error(f"Erro ao buscar detalhes do log {log_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar detalhes: {str(e)}")


@router.get("/rastrear/{entidade}/{entidade_id}", response_model=List[AuditoriaResponse])
async def rastrear_entidade(
    entidade: str,
    entidade_id: str,
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Rastrear todas as ações em uma entidade específica.
    
    **Requer ADMIN**
    
    Exemplo: /auditoria/rastrear/reserva/123
    """
    try:
        db = get_db()
        
        logs = await db.auditoria.find_many(
            where={
                "entidade": entidade.upper(),
                "entidadeId": str(entidade_id)
            },
            include={
                "funcionario": True
            },
            order={"createdAt": "desc"},
            take=100
        )
        
        resposta = []
        for log in logs:
            resposta.append(AuditoriaResponse(
                id=log.id,
                funcionario_id=log.funcionarioId,
                funcionario_nome=log.funcionario.nome if log.funcionario else None,
                entidade=log.entidade,
                entidade_id=log.entidadeId,
                acao=log.acao,
                payload_resumo=log.payloadResumo,
                ip_address=log.ipAddress,
                user_agent=log.userAgent,
                created_at=log.createdAt.isoformat()
            ))
        
        audit_logger.info(
            f"Rastreamento da entidade {entidade}:{entidade_id} "
            f"por admin {current_user.id}: {len(resposta)} ações encontradas"
        )
        
        return resposta
        
    except Exception as e:
        audit_logger.error(f"Erro ao rastrear entidade {entidade}:{entidade_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao rastrear entidade: {str(e)}")


@router.get("/atividade-usuario/{usuario_id}", response_model=List[AuditoriaResponse])
async def atividade_usuario(
    usuario_id: int,
    dias: int = Query(30, ge=1, le=90, description="Número de dias para análise"),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Obter atividade completa de um usuário específico.
    
    **Requer ADMIN**
    """
    try:
        db = get_db()
        
        # Calcular data de corte
        data_corte = datetime.now() - timedelta(days=dias)
        
        logs = await db.auditoria.find_many(
            where={
                "funcionarioId": usuario_id,
                "createdAt": {"gte": data_corte}
            },
            include={
                "funcionario": True
            },
            order={"createdAt": "desc"},
            take=500
        )
        
        resposta = []
        for log in logs:
            resposta.append(AuditoriaResponse(
                id=log.id,
                funcionario_id=log.funcionarioId,
                funcionario_nome=log.funcionario.nome if log.funcionario else None,
                entidade=log.entidade,
                entidade_id=log.entidadeId,
                acao=log.acao,
                payload_resumo=log.payloadResumo,
                ip_address=log.ipAddress,
                user_agent=log.userAgent,
                created_at=log.createdAt.isoformat()
            ))
        
        audit_logger.info(
            f"Atividade do funcionário {usuario_id} consultada por admin {current_user.id}: "
            f"{len(resposta)} ações encontradas"
        )
        
        return resposta
        
    except Exception as e:
        audit_logger.error(f"Erro ao consultar atividade do usuário {usuario_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar atividade: {str(e)}")
