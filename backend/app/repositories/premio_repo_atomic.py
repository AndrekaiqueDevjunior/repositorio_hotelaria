"""
Repositório de Prêmios com Transações Atômicas
Implementa resgate de prêmios com lock pessimista para prevenir race conditions
"""
from typing import Dict, Any, List, Optional
from prisma import Client
import logging
import secrets
from datetime import timedelta

from app.utils.datetime_utils import now_utc

security_logger = logging.getLogger("security")
CODIGO_STATUS_ACTIVE = "active"
CODIGO_STATUS_USED = "used"
CODIGO_STATUS_EXPIRED = "expired"


class PremioRepositoryAtomic:
    """
    Repositório de prêmios com transações atômicas.
    Usa SELECT FOR UPDATE para prevenir race conditions no resgate.
    """
    
    def __init__(self, db: Client):
        self.db = db
    
    async def list_all(self, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        """Listar todos os prêmios disponíveis"""
        where = {"ativo": True} if apenas_ativos else {}
        
        premios = await self.db.premio.find_many(
            where=where,
            order={"precoEmPontos": "asc"}
        )
        
        return [self._serialize(p) for p in premios]
    
    async def get_by_id(self, premio_id: int) -> Optional[Dict[str, Any]]:
        """Obter prêmio por ID"""
        premio = await self.db.premio.find_unique(where={"id": premio_id})
        if not premio:
            return None
        return self._serialize(premio)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar novo prêmio"""
        preco_rp = data.get("preco_em_rp")
        if preco_rp is None:
            preco_rp = 0
        
        premio = await self.db.premio.create(
            data={
                "nome": data["nome"],
                "descricao": data.get("descricao"),
                "precoEmPontos": data["preco_em_pontos"],
                "precoEmRp": preco_rp,
                "ativo": data.get("ativo", True),
                "categoria": data.get("categoria", "GERAL"),
                "estoque": data.get("estoque"),
                "imagemUrl": data.get("imagem_url")
            }
        )
        return self._serialize(premio)
    
    async def update(self, premio_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualizar prêmio"""
        premio = await self.db.premio.find_unique(where={"id": premio_id})
        if not premio:
            return None
        
        update_data = {}
        if "nome" in data:
            update_data["nome"] = data["nome"]
        if "descricao" in data:
            update_data["descricao"] = data["descricao"]
        if "preco_em_pontos" in data:
            update_data["precoEmPontos"] = data["preco_em_pontos"]
        if "preco_em_rp" in data:
            update_data["precoEmRp"] = data["preco_em_rp"]
        if "ativo" in data:
            update_data["ativo"] = data["ativo"]
        if "categoria" in data:
            update_data["categoria"] = data["categoria"]
        if "estoque" in data:
            update_data["estoque"] = data["estoque"]
        if "imagem_url" in data:
            update_data["imagemUrl"] = data["imagem_url"]
        
        if not update_data:
            return self._serialize(premio)
        
        premio_atualizado = await self.db.premio.update(
            where={"id": premio_id},
            data=update_data
        )
        return self._serialize(premio_atualizado)
    
    async def delete(self, premio_id: int) -> bool:
        """Desativar prêmio (soft delete)"""
        premio = await self.db.premio.find_unique(where={"id": premio_id})
        if not premio:
            return False
        
        await self.db.premio.update(
            where={"id": premio_id},
            data={"ativo": False}
        )
        return True
    
    async def resgatar_atomic(
        self, 
        premio_id: int, 
        cliente_id: int,
        funcionario_id: int = None
    ) -> Dict[str, Any]:
        """
        Resgatar prêmio com transação atômica e lock pessimista.
        
        PROTEÇÃO CONTRA RACE CONDITION:
        - Transação atômica para todas as operações
        - Lock no prêmio (estoque) e pontos do cliente
        - Commit ou rollback completo
        
        Fluxo:
        1. Lock no prêmio (verificar estoque)
        2. Lock nos pontos do cliente (verificar saldo)
        3. Debitar pontos
        4. Decrementar estoque
        5. Criar registro de resgate
        6. Commit (ou rollback se qualquer operação falhar)
        """
        from app.repositories.pontos_repo_atomic import PontosRepositoryAtomic
        
        # TRANSAÇÃO ATÔMICA COMPLETA
        async with self.db.tx() as transaction:
            # 1. LOCK NO PRÊMIO (SELECT FOR UPDATE)
            premio_raw = await transaction.query_raw(
                """
                SELECT * FROM premios 
                WHERE id = $1 
                FOR UPDATE
                """,
                premio_id
            )
            
            if not premio_raw:
                return {"success": False, "error": "Prêmio não encontrado"}
            
            premio_data = premio_raw[0]
            
            # Validações do prêmio
            if not premio_data['ativo']:
                return {"success": False, "error": "Prêmio não está ativo"}
            
            # VALIDAÇÃO CRÍTICA: Estoque
            estoque_atual = premio_data.get('estoque')
            if estoque_atual is not None and estoque_atual <= 0:
                security_logger.warning(
                    f"Tentativa de resgate com estoque esgotado - "
                    f"Premio: {premio_id}, Cliente: {cliente_id}, Estoque: {estoque_atual}"
                )
                return {"success": False, "error": "Prêmio sem estoque disponível"}
            
            custo = premio_data['preco_em_pontos']
            
            # 2. LOCK NOS PONTOS DO CLIENTE (SELECT FOR UPDATE)
            usuario_pontos_raw = await transaction.query_raw(
                """
                SELECT * FROM usuarios_pontos 
                WHERE cliente_id = $1 
                FOR UPDATE
                """,
                cliente_id
            )
            
            if not usuario_pontos_raw:
                # Criar registro se não existir
                usuario_pontos = await transaction.usuariopontos.create(
                    data={"clienteId": cliente_id, "saldo": 0}
                )
                saldo_atual = 0
                usuario_pontos_id = usuario_pontos.id
            else:
                usuario_pontos_data = usuario_pontos_raw[0]
                saldo_atual = usuario_pontos_data['saldo']
                usuario_pontos_id = usuario_pontos_data['id']
            
            # VALIDAÇÃO CRÍTICA: Saldo
            if saldo_atual < custo:
                security_logger.warning(
                    f"Tentativa de resgate com saldo insuficiente - "
                    f"Cliente: {cliente_id}, Saldo: {saldo_atual}, Custo: {custo}"
                )
                return {
                    "success": False, 
                    "error": f"Saldo insuficiente. Necessário: {custo} pontos. Disponível: {saldo_atual} pontos"
                }
            
            # 3. DEBITAR PONTOS (dentro da transação)
            novo_saldo = saldo_atual - custo
            
            await transaction.execute_raw(
                """
                UPDATE usuarios_pontos 
                SET saldo = $1, updated_at = NOW()
                WHERE id = $2
                """,
                novo_saldo,
                usuario_pontos_id
            )
            
            # Criar registro de transação de pontos
            transacao_pontos = await transaction.transacaopontos.create(
                data={
                    "clienteId": cliente_id,
                    "usuarioPontosId": usuario_pontos_id,
                    "funcionarioId": funcionario_id,
                    "tipo": "RESGATE",
                    "origem": "PREMIO",
                    "pontos": -custo,
                    "saldoAnterior": saldo_atual,
                    "saldoPosterior": novo_saldo,
                    "motivo": f"Resgate de prêmio: {premio_data['nome']}"
                }
            )
            
            # 4. DECREMENTAR ESTOQUE (se aplicável)
            if estoque_atual is not None:
                await transaction.execute_raw(
                    """
                    UPDATE premios 
                    SET estoque = estoque - 1, updated_at = NOW()
                    WHERE id = $1 AND estoque > 0
                    """,
                    premio_id
                )
                
                # Verificar se o update afetou alguma linha
                # Se não afetou, significa que estoque zerou entre a verificação e o update
                estoque_verificacao = await transaction.query_raw(
                    "SELECT estoque FROM premios WHERE id = $1",
                    premio_id
                )
                
                if estoque_verificacao and estoque_verificacao[0]['estoque'] < 0:
                    security_logger.error(
                        f"Race condition detectada no estoque - "
                        f"Premio: {premio_id}, Estoque ficou negativo!"
                    )
                    # Rollback automático ao lançar exceção
                    raise Exception("Estoque esgotado durante o processamento")
            
            codigo_resgate = await self._gerar_codigo_resgate(transaction)
            expira_em = now_utc() + timedelta(days=30)

            # 5. CRIAR REGISTRO DE RESGATE
            resgate = await transaction.resgatepremio.create(
                data={
                    "clienteId": cliente_id,
                    "premioId": premio_id,
                    "pontosUsados": custo,
                    "status": "PENDENTE",
                    "codigoResgate": codigo_resgate,
                    "codigoStatus": CODIGO_STATUS_ACTIVE,
                    "expiraEm": expira_em,
                    "funcionarioId": funcionario_id
                }
            )
            
            # 6. BUSCAR DADOS DO CLIENTE PARA NOTIFICAÇÃO
            cliente_raw = await transaction.query_raw(
                'SELECT "nomeCompleto", telefone, "enderecoCompleto" FROM clientes WHERE id = $1',
                cliente_id
            )
            
            cliente_dados = cliente_raw[0] if cliente_raw else {}
            cliente_nome = cliente_dados.get('nomeCompleto', 'Cliente')
            cliente_telefone = cliente_dados.get('telefone')
            cliente_endereco = cliente_dados.get('enderecoCompleto')
            
            security_logger.info(
                f"Resgate atômico realizado com sucesso - "
                f"Cliente: {cliente_id}, Premio: {premio_id} ({premio_data['nome']}), "
                f"Pontos: {custo}, Saldo: {saldo_atual} → {novo_saldo}, "
                f"Estoque: {estoque_atual} → {estoque_atual - 1 if estoque_atual else 'N/A'}"
            )
            
            # Commit automático ao sair do bloco 'async with'
            result = {
                "success": True,
                "resgate_id": resgate.id,
                "premio": {
                    "id": premio_data['id'],
                    "nome": premio_data['nome'],
                    "preco_em_pontos": premio_data['preco_em_pontos']
                },
                "pontos_usados": custo,
                "novo_saldo": novo_saldo,
                "transacao_id": transacao_pontos.id,
                "cliente_nome": cliente_nome,
                "codigo_resgate": codigo_resgate,
                "codigo_status": CODIGO_STATUS_ACTIVE,
                "expira_em": expira_em.isoformat()
            }
        
        # 7. ENVIAR NOTIFICAÇÃO WHATSAPP (FORA DA TRANSAÇÃO)
        try:
            from app.services.whatsapp_service import get_whatsapp_service
            
            whatsapp_service = get_whatsapp_service()
            notificacao_result = await whatsapp_service.enviar_notificacao_resgate_premio(
                cliente_nome=cliente_nome,
                cliente_telefone=cliente_telefone,
                cliente_endereco=cliente_endereco,
                premio_nome=premio_data['nome'],
                pontos_usados=custo,
                codigo_resgate=codigo_resgate
            )
            
            if notificacao_result.get("success"):
                security_logger.info(
                    f"Notificação WhatsApp enviada - Resgate: {resgate.id}, "
                    f"SID: {notificacao_result.get('message_sid')}"
                )
            else:
                security_logger.warning(
                    f"Falha ao enviar WhatsApp - Resgate: {resgate.id}, "
                    f"Erro: {notificacao_result.get('error')}"
                )
        except Exception as e:
            # Não falhar o resgate se WhatsApp falhar
            security_logger.error(f"Erro ao enviar notificação WhatsApp: {str(e)}")
        
        return result

    async def usar_codigo_resgate(
        self,
        codigo_resgate: str,
        funcionario_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        codigo = (codigo_resgate or "").strip().upper()
        if not codigo:
            return {"success": False, "error": "Codigo de resgate obrigatorio"}

        async with self.db.tx() as transaction:
            rows = await transaction.query_raw(
                """
                SELECT *
                FROM resgates_premios
                WHERE codigo_resgate = $1
                FOR UPDATE
                """,
                codigo,
            )
            if not rows:
                return {"success": False, "error": "Codigo de resgate nao encontrado"}

            resgate = rows[0]
            status_codigo = (resgate.get("codigo_status") or CODIGO_STATUS_ACTIVE).lower()
            if status_codigo != CODIGO_STATUS_ACTIVE:
                return {"success": False, "error": f"Codigo ja inutilizado: {status_codigo}"}

            expira_em = resgate.get("expira_em")
            if expira_em and expira_em < now_utc():
                await transaction.execute_raw(
                    """
                    UPDATE resgates_premios
                    SET codigo_status = $1, updated_at = NOW()
                    WHERE id = $2
                    """,
                    CODIGO_STATUS_EXPIRED,
                    int(resgate["id"]),
                )
                return {"success": False, "error": "Codigo expirado"}

            usado_em = now_utc()
            await transaction.execute_raw(
                """
                UPDATE resgates_premios
                SET codigo_status = $1,
                    usado_em = $2,
                    status = 'ENTREGUE',
                    funcionario_entrega_id = $3,
                    updated_at = NOW()
                WHERE id = $4
                """,
                CODIGO_STATUS_USED,
                usado_em,
                funcionario_id,
                int(resgate["id"]),
            )

            return {
                "success": True,
                "resgate_id": int(resgate["id"]),
                "codigo_resgate": codigo,
                "codigo_status": CODIGO_STATUS_USED,
                "usado_em": usado_em.isoformat(),
            }

    async def listar_resgates_cliente(self, cliente_id: int) -> List[Dict[str, Any]]:
        """Listar resgates de um cliente"""
        resgates = await self.db.resgatepremio.find_many(
            where={"clienteId": cliente_id},
            include={"premio": True},
            order={"createdAt": "desc"}
        )
        
        return [
            {
                "id": r.id,
                "premio_id": r.premioId,
                "premio_nome": r.premio.nome if r.premio else None,
                "pontos_usados": r.pontosUsados,
                "status": r.status,
                "codigo_resgate": getattr(r, "codigoResgate", None),
                "codigo_status": getattr(r, "codigoStatus", None),
                "expira_em": getattr(r, "expiraEm", None).isoformat() if getattr(r, "expiraEm", None) else None,
                "usado_em": getattr(r, "usadoEm", None).isoformat() if getattr(r, "usadoEm", None) else None,
                "data_resgate": r.createdAt.isoformat() if r.createdAt else None
            }
            for r in resgates
        ]
    
    async def confirmar_entrega(self, resgate_id: int, funcionario_id: int) -> Dict[str, Any]:
        """Confirmar entrega de prêmio resgatado"""
        resgate = await self.db.resgatepremio.find_unique(where={"id": resgate_id})
        if not resgate:
            return {"success": False, "error": "Resgate não encontrado"}
        
        if resgate.status == "ENTREGUE" or getattr(resgate, "codigoStatus", None) == CODIGO_STATUS_USED:
            return {"success": False, "error": "Prêmio já foi entregue"}
        
        await self.db.resgatepremio.update(
            where={"id": resgate_id},
            data={
                "status": "ENTREGUE",
                "funcionarioEntregaId": funcionario_id,
                "codigoStatus": CODIGO_STATUS_USED,
                "usadoEm": now_utc(),
            }
        )
        
        return {"success": True, "message": "Entrega confirmada"}
    
    def _serialize(self, premio) -> Dict[str, Any]:
        """Serializar prêmio para response"""
        return {
            "id": premio.id,
            "nome": premio.nome,
            "descricao": getattr(premio, "descricao", None),
            "preco_em_pontos": premio.precoEmPontos,
            "preco_em_rp": getattr(premio, "precoEmRp", premio.precoEmPontos),
            "ativo": premio.ativo,
            "categoria": getattr(premio, "categoria", "GERAL"),
            "estoque": getattr(premio, "estoque", None),
            "imagem_url": getattr(premio, "imagemUrl", None),
            "created_at": premio.createdAt.isoformat() if premio.createdAt else None
        }

    async def _gerar_codigo_resgate(self, transaction) -> str:
        for _tentativa in range(10):
            codigo = f"RW-{secrets.token_hex(3).upper()}"
            rows = await transaction.query_raw(
                "SELECT id FROM resgates_premios WHERE codigo_resgate = $1 LIMIT 1",
                codigo,
            )
            if not rows:
                return codigo
        raise ValueError("Nao foi possivel gerar codigo unico de resgate")
