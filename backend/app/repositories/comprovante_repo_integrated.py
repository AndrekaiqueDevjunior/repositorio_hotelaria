"""
Versão integrada do ComprovanteRepository com transições automáticas
Mostra como aplicar StateTransitionService nos repositórios existentes
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from prisma import Client
from app.schemas.comprovante_schema import (
    ComprovanteUpload, 
    ValidacaoPagamento,
    TipoComprovante,
    StatusValidacao
)
from app.utils.datetime_utils import now_utc
from app.services.notification_service import NotificationService
from app.core.state_transition_service import StateTransitionService
import base64
import os
import uuid
import re


class ComprovanteRepositoryIntegrated:
    """
    ComprovanteRepository com transições automáticas de estado integradas
    """
    
    def __init__(self, db: Client):
        self.db = db
        self.state_service = StateTransitionService(db)
    
    def _sanitizar_nome(self, nome: str) -> str:
        """Sanitiza nome para uso em caminhos de arquivo"""
        nome = re.sub(r'[^\w\s-]', '', nome)
        nome = re.sub(r'\s+', '_', nome)
        nome = re.sub(r'_+', '_', nome)
        return nome[:50].strip('_').lower()
    
    async def upload_comprovante(self, dados: ComprovanteUpload) -> Dict[str, Any]:
        """
        Upload de comprovante COM transição automática de estado
        
        NOVO FLUXO:
        1. Validar pagamento
        2. Salvar arquivo
        3. Criar comprovante
        4. Atualizar pagamento
        5. ⭐ EXECUTAR TRANSIÇÃO AUTOMÁTICA: AGUARDANDO_COMPROVANTE → EM_ANALISE
        """
        # 1. Validar pagamento
        pagamento = await self.db.pagamento.find_unique(
            where={"id": dados.pagamento_id},
            include={"cliente": True, "reserva": True}
        )
        if not pagamento:
            raise ValueError(f"Pagamento {dados.pagamento_id} não encontrado")
        
        # 2. Salvar arquivo (mesma lógica original)
        cliente = pagamento.cliente
        cliente_id = cliente.id
        cliente_nome = self._sanitizar_nome(cliente.nomeCompleto)
        
        agora = now_utc()
        ano = agora.strftime("%Y")
        mes = agora.strftime("%m")
        
        pasta_cliente = f"uploads/comprovantes/{cliente_id}_{cliente_nome}"
        pasta_ano = f"{pasta_cliente}/{ano}"
        pasta_mes = f"{pasta_ano}/{mes}"
        
        os.makedirs(pasta_mes, exist_ok=True)
        
        timestamp = agora.strftime("%Y%m%d_%H%M%S")
        extensao = os.path.splitext(dados.nome_arquivo)[1]
        nome_arquivo = f"comprovante_pag{dados.pagamento_id}_{timestamp}_{uuid.uuid4().hex[:8]}{extensao}"
        caminho_arquivo = f"{pasta_mes}/{nome_arquivo}"
        
        try:
            arquivo_bytes = base64.b64decode(dados.arquivo_base64)
            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo_bytes)
        except Exception as e:
            raise ValueError(f"Erro ao salvar arquivo: {str(e)}")
        
        # 3. Criar comprovante
        comprovante = await self.db.comprovantepagamento.create(
            data={
                "pagamentoId": dados.pagamento_id,
                "tipoComprovante": dados.tipo_comprovante.value,
                "nomeArquivo": nome_arquivo,
                "caminhoArquivo": caminho_arquivo,
                "observacoes": dados.observacoes,
                "valorConfirmado": dados.valor_confirmado,
                "statusValidacao": StatusValidacao.AGUARDANDO_COMPROVANTE.value,
                "dataUpload": agora,
            }
        )
        
        # 4. Atualizar pagamento
        await self.db.pagamento.update(
            where={"id": dados.pagamento_id},
            data={"statusPagamento": "PENDENTE", "updatedAt": agora}
        )
        
        # 5. ⭐ NOVO: Executar transição automática de estado
        transicao_result = await self.state_service.transicao_apos_upload_comprovante(dados.pagamento_id)
        
        if transicao_result["success"]:
            print(f"[TRANSICAO] {transicao_result['transicao']} - Reserva {pagamento.reservaId}")
        
        # 6. Criar notificação (mesma lógica original)
        try:
            notification_service = NotificationService(self.db)
            await notification_service.criar_notificacao(
                titulo="📤 Novo Comprovante Recebido",
                mensagem=f"Cliente: {cliente.nomeCompleto} | Valor: R$ {float(dados.valor_confirmado or 0):.2f} | Tipo: {dados.tipo_comprovante.value}",
                tipo="info",
                categoria="pagamento",
                perfil="ADMIN,RECEPCAO",
                pagamento_id=dados.pagamento_id,
                reserva_id=pagamento.reservaId,
                url_acao=f"/comprovantes"
            )
        except Exception as e:
            print(f"[NOTIFICAÇÃO] Erro: {str(e)}")
        
        return {
            "success": True,
            "comprovante": comprovante,
            "message": f"Comprovante enviado! Aguardando validação.",
            "transicao_estado": transicao_result,
            "status_reserva": transicao_result.get("novo_status"),
            "caminho": caminho_arquivo
        }
    
    async def validar_comprovante(self, dados: ValidacaoPagamento) -> Dict[str, Any]:
        """
        Validação de comprovante COM transições automáticas de estado
        
        NOVO FLUXO:
        1. Buscar comprovante
        2. Atualizar status do comprovante
        3. Atualizar pagamento
        4. ⭐ EXECUTAR TRANSIÇÃO AUTOMÁTICA:
           - Se APROVADO: EM_ANALISE → CONFIRMADA + criar hospedagem
           - Se RECUSADO: EM_ANALISE → PAGA_REJEITADA
        5. Notificações
        """
        # 1. Buscar comprovante
        comprovante = await self.db.comprovantepagamento.find_first(
            where={"pagamentoId": dados.pagamento_id}
        )
        if not comprovante:
            raise ValueError(f"Comprovante não encontrado para pagamento {dados.pagamento_id}")
        
        # 2. Atualizar status do comprovante
        comprovante_atualizado = await self.db.comprobantepagamento.update(
            where={"id": comprovante.id},
            data={
                "statusValidacao": dados.status.value,
                "dataValidacao": now_utc(),
                "validadorId": dados.usuario_validador_id,
                "motivoRecusa": dados.motivo if dados.status == StatusValidacao.RECUSADO else None,
                "observacoesInternas": dados.observacoes_internas,
            }
        )
        
        # 3. Atualizar pagamento
        status_pagamento = "CONFIRMADO" if dados.status == StatusValidacao.APROVADO else "NEGADO"
        await self.db.pagamento.update(
            where={"id": dados.pagamento_id},
            data={"statusPagamento": status_pagamento, "updatedAt": now_utc()}
        )
        
        # 4. ⭐ NOVO: Executar transição automática baseada na validação
        if dados.status == StatusValidacao.APROVADO:
            transicao_result = await self.state_service.transicao_apos_aprovacao_pagamento(
                dados.pagamento_id, dados.usuario_validador_id
            )
        else:
            transicao_result = await self.state_service.transicao_apos_recusa_pagamento(
                dados.pagamento_id, dados.usuario_validador_id
            )
        
        if transicao_result["success"]:
            print(f"[TRANSICAO] {transicao_result['transicao']} - Reserva {transicao_result.get('reserva_id')}")
        
        # 5. Notificações (mesma lógica original)
        try:
            notification_service = NotificationService(self.db)
            pagamento = await self.db.pagamento.find_unique(
                where={"id": dados.pagamento_id},
                include={"cliente": True, "reserva": True}
            )
            
            if dados.status == StatusValidacao.APROVADO:
                await notification_service.criar_notificacao(
                    titulo="✅ Comprovante Aprovado",
                    mensagem=f"Pagamento de R$ {float(pagamento.valor):.2f} aprovado | Cliente: {pagamento.cliente.nomeCompleto}",
                    tipo="success",
                    categoria="pagamento",
                    perfil="ADMIN,RECEPCAO",
                    pagamento_id=dados.pagamento_id,
                    reserva_id=pagamento.reservaId,
                    url_acao=f"/pagamentos"
                )
            else:
                await notification_service.criar_notificacao(
                    titulo="❌ Comprovante Recusado",
                    mensagem=f"Pagamento de R$ {float(pagamento.valor):.2f} recusado | Motivo: {dados.motivo}",
                    tipo="warning",
                    categoria="pagamento",
                    perfil="ADMIN,RECEPCAO",
                    pagamento_id=dados.pagamento_id,
                    reserva_id=pagamento.reservaId,
                    url_acao=f"/pagamentos"
                )
        except Exception as e:
            print(f"[NOTIFICAÇÃO] Erro: {str(e)}")
        
        return {
            "success": True,
            "comprovante": comprovante_atualizado,
            "message": f"Pagamento {dados.status.value} com sucesso!",
            "transicao_estado": transicao_result,
            "status_reserva": transicao_result.get("novo_status"),
            "hospedagem_criada": transicao_result.get("hospedagem_criada", False)
        }
    
    async def diagnosticar_reserva(self, reserva_id: int) -> Dict[str, Any]:
        """
        Diagnóstico completo do estado da reserva
        """
        return await self.state_service.diagnosticar_reserva(reserva_id)


# ==================== EXEMPLO DE INTEGRAÇÃO ====================

"""
Para usar o novo repositório integrado:

1. Substituir a importação no comprovante_routes.py:

DE:
from app.repositories.comprovante_repo import ComprovanteRepository

PARA:
from app.repositories.comprovante_repo_integrated import ComprovanteRepositoryIntegrated

2. Atualizar a injeção de dependência:

DE:
comprovante_repo = ComprovanteRepository(db)

PARA:
comprovante_repo = ComprovanteRepositoryIntegrated(db)

3. O frontend receberá automaticamente os status atualizados:
   - Após upload: status muda para EM_ANALISE
   - Após aprovação: status muda para CONFIRMADA
   - Após recusa: status muda para PAGA_REJEITADA

4. A hospedagem será criada automaticamente na aprovação

Benefícios:
- ✅ Transições automáticas de estado
- ✅ Consistência entre frontend e backend
- ✅ Fluxo completo funcional
- ✅ Check-in habilitado automaticamente
"""
