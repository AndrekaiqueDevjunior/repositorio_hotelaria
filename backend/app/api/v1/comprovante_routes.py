"""
API Routes para Comprovação de Pagamentos

Endpoints para upload, validação e gestão de comprovantes de pagamento.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from app.schemas.comprovante_schema import (
    ComprovanteUpload,
    ValidacaoPagamento,
    DashboardValidacao,
    TipoComprovante,
    StatusValidacao
)
from app.repositories.comprovante_repo import ComprovanteRepository
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.core.enums import PerfilUsuario
from typing import List, Dict, Any
import os

router = APIRouter(prefix="/comprovantes", tags=["comprovantes"])

# Dependency injection
async def get_comprovante_repo() -> ComprovanteRepository:
    db = get_db()
    return ComprovanteRepository(db)

@router.post("/upload", response_model=dict)
async def upload_comprovante(
    dados: ComprovanteUpload,
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fazer upload de comprovante de pagamento
    
    Acesso: CLIENTE pode上传自己的comprovante
    """
    try:
        print(f"[UPLOAD] Recebido upload de comprovante:")
        print(f"  - pagamento_id: {dados.pagamento_id}")
        print(f"  - tipo_comprovante: {dados.tipo_comprovante}")
        print(f"  - nome_arquivo: {dados.nome_arquivo}")
        print(f"  - arquivo_base64 length: {len(dados.arquivo_base64) if dados.arquivo_base64 else 0}")
        print(f"  - valor_confirmado: {dados.valor_confirmado}")
        
        # Validar se o usuário tem permissão para este pagamento
        db = get_db()
        pagamento = await db.pagamento.find_unique(
            where={"id": dados.pagamento_id},
            include={"reserva": True}
        )
        
        if not pagamento:
            raise ValueError(f"Pagamento {dados.pagamento_id} não encontrado")
        
        # Staff pode fazer upload em qualquer pagamento
        if current_user.perfil not in [PerfilUsuario.ADMIN, PerfilUsuario.GERENTE, PerfilUsuario.RECEPCAO, PerfilUsuario.FUNCIONARIO]:
            # Para clientes, verificar se o pagamento pertence ao usuário
            if not pagamento.reserva or pagamento.reserva.clienteId != current_user.id:
                raise ValueError("Acesso negado: este pagamento não pertence a você")
        
        result = await repo.upload_comprovante(dados)
        return result
    except ValueError as e:
        print(f"[UPLOAD ERROR] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[UPLOAD ERROR] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")

@router.post("/validar", response_model=dict)
async def validar_comprovante(
    dados: ValidacaoPagamento,
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Validar comprovante de pagamento
    
    Acesso: ADMIN ou GERENTE apenas
    """
    try:
        result = await repo.validar_comprovante(dados)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao validar: {str(e)}")

@router.get("/pendentes", response_model=List[dict])
async def listar_pendentes_validacao(
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Listar comprovantes aguardando validação
    
    Acesso: ADMIN ou GERENTE apenas
    """
    try:
        return await repo.listar_pendentes_validacao()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar pendentes: {str(e)}")

@router.get("/em-analise", response_model=List[dict])
async def listar_em_analise(
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Listar comprovantes em análise
    
    Acesso: ADMIN ou GERENTE apenas
    """
    try:
        return await repo.listar_em_analise()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar em análise: {str(e)}")

@router.get("/dashboard")
async def dashboard_validacao(
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Dashboard de validação de comprovantes
    
    Acesso: ADMIN ou GERENTE apenas
    """
    try:
        stats = await repo.dashboard_validacao()
        
        # Buscar listas detalhadas
        pendentes = await repo.listar_pendentes_validacao()
        em_analise = await repo.listar_em_analise()

        return {
            "aguardando_comprovante": pendentes,
            "em_analise": em_analise,
            "aprovados_hoje": [],  # TODO: Implementar lista de aprovados hoje
            "recusados_hoje": [],  # TODO: Implementar lista de recusados hoje
            "estatisticas": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar dashboard: {str(e)}")

@router.get("/arquivo/{nome_arquivo}")
async def visualizar_comprovante(
    nome_arquivo: str,
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(get_current_active_user)
):
    """
    Visualizar arquivo de comprovante em nova aba
    
    Acesso: Usuário autenticado com permissão
    - Cliente: apenas seus próprios comprovantes
    - Staff: todos os comprovantes
    """
    try:
        # Validar se o comprovante existe
        comprovante = await repo.get_comprovante_by_arquivo(nome_arquivo)
        if not comprovante:
            raise HTTPException(status_code=404, detail="Comprovante não encontrado")
        
        # Validar permissão de acesso
        # Staff pode acessar qualquer comprovante
        if current_user.perfil not in [PerfilUsuario.ADMIN, PerfilUsuario.GERENTE, PerfilUsuario.RECEPCAO, PerfilUsuario.FUNCIONARIO]:
            # Para clientes, verificar se o comprovante pertence ao usuário
            # Nota: Esta lógica assume que clientes também usam User model. 
            # Se clientes usam modelo diferente, ajustar conforme necessário.
            db = get_db()
            pagamento = await db.pagamento.find_unique(
                where={"id": comprovante.get("pagamento_id")}
            )
            if not pagamento:
                raise HTTPException(status_code=404, detail="Pagamento não encontrado")
            
            reserva = await db.reserva.find_unique(
                where={"id": pagamento.reservaId}
            )
            if not reserva or reserva.clienteId != current_user.id:
                raise HTTPException(status_code=403, detail="Acesso negado a este comprovante")
        
        # Montar caminho do arquivo (usar caminho salvo no banco)
        caminho_arquivo = getattr(comprovante, "caminhoArquivo", None) or comprovante.get("caminhoArquivo")
        
        from pathlib import Path
        if not caminho_arquivo or not Path(caminho_arquivo).exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        filename = getattr(comprovante, "nomeArquivo", None) or comprovante.get("nomeArquivo") or nome_arquivo
        
        # Determinar o media type baseado na extensão do arquivo
        from pathlib import Path
        file_extension = Path(filename).suffix.lower()
        
        media_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        media_type = media_types.get(file_extension, 'application/octet-stream')
        
        # Para PDF, usar headers que incentivam visualização em nova aba
        headers = {}
        if media_type == 'application/pdf':
            headers = {
                'Content-Disposition': f'inline; filename="{filename}"',
                'Content-Type': media_type
            }
        else:
            headers = {
                'Content-Disposition': f'inline; filename="{filename}"',
                'Content-Type': media_type
            }
        
        return FileResponse(
            path=caminho_arquivo,
            filename=filename,
            media_type=media_type,
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao visualizar arquivo: {str(e)}")

@router.post("/{pagamento_id}/aprovar-rapido")
async def aprovar_pagamento_rapido(
    pagamento_id: int,
    motivo: str = "Pagamento aprovado manualmente",
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Aprovar pagamento rapidamente (sem upload de comprovante)
    
    Para casos como:
    - Pagamento em dinheiro recebido presencialmente
    - Pagamento já confirmado por outro meio
    
    Acesso: ADMIN ou GERENTE apenas
    """
    try:
        # Criar validação direta
        validacao = ValidacaoPagamento(
            pagamento_id=pagamento_id,
            status=StatusValidacao.APROVADO,
            motivo=motivo,
            usuario_validador_id=current_user.id,
            observacoes_internas="Aprovação rápida sem comprovante"
        )
        
        result = await repo.validar_comprovante(validacao)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao aprovar pagamento: {str(e)}")

@router.post("/{pagamento_id}/recusar")
async def recusar_pagamento(
    pagamento_id: int,
    motivo: str,
    observacoes_internas: str = None,
    repo: ComprovanteRepository = Depends(get_comprovante_repo),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Recusar pagamento
    
    Acesso: ADMIN ou GERENTE apenas
    """
    try:
        validacao = ValidacaoPagamento(
            pagamento_id=pagamento_id,
            status=StatusValidacao.RECUSADO,
            motivo=motivo,
            usuario_validador_id=current_user.id,
            observacoes_internas=observacoes_internas
        )
        
        result = await repo.validar_comprovante(validacao)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recusar pagamento: {str(e)}")
