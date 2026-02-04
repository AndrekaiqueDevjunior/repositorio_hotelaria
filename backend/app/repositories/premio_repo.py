"""
Repositório para gerenciamento de prêmios do sistema de fidelidade.
"""
from typing import Dict, Any, List, Optional
from prisma import Client


class PremioRepository:
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
        # Garantir que precoEmRp tenha um valor válido
        preco_rp = data.get("preco_em_rp")
        if preco_rp is None:
            preco_rp = 0  # Valor padrão conforme schema
        
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
    
    async def resgatar(
        self, 
        premio_id: int, 
        cliente_id: int,
        funcionario_id: int = None
    ) -> Dict[str, Any]:
        """
        Resgatar prêmio usando pontos do cliente.
        
        Retorna:
            - success: bool
            - resgate_id: int (se sucesso)
            - error: str (se falha)
        """
        from app.repositories.pontos_repo import PontosRepository
        import logging
        
        security_logger = logging.getLogger("security")
        
        # Verificar se prêmio existe e está ativo
        premio = await self.db.premio.find_unique(where={"id": premio_id})
        if not premio:
            return {"success": False, "error": "Prêmio não encontrado"}
        
        if not premio.ativo:
            return {"success": False, "error": "Prêmio não está ativo"}
        
        # VALIDAÇÃO DE SEGURANÇA: Verificar estoque ANTES de qualquer operação
        if premio.estoque is not None and premio.estoque <= 0:
            security_logger.warning(
                f"Tentativa de resgate com estoque esgotado - "
                f"Premio: {premio_id}, Cliente: {cliente_id}"
            )
            return {"success": False, "error": "Prêmio sem estoque disponível"}
        
        custo = premio.precoEmPontos
        
        # Verificar saldo do cliente
        db = await get_db_connected()
        pontos_repo = PontosRepository(db)
        saldo_data = await pontos_repo.get_saldo(cliente_id)
        saldo_atual = saldo_data.get("saldo", 0)
        
        if saldo_atual < custo:
            return {
                "success": False, 
                "error": f"Saldo insuficiente. Necessário: {custo} pontos. Disponível: {saldo_atual} pontos"
            }
        
        # Debitar pontos
        result = await pontos_repo.criar_transacao_pontos(
            cliente_id=cliente_id,
            pontos=-custo,
            tipo="RESGATE",
            origem="PREMIO",
            motivo=f"Resgate de prêmio: {premio.nome}",
            reserva_id=None,
            funcionario_id=funcionario_id
        )
        
        if not result.get("success"):
            return {"success": False, "error": "Falha ao debitar pontos"}
        
        # Criar registro de resgate
        resgate = await self.db.resgatepremio.create(
            data={
                "clienteId": cliente_id,
                "premioId": premio_id,
                "pontosUsados": custo,
                "status": "PENDENTE",
                "funcionarioId": funcionario_id
            }
        )
        
        # ATUALIZAÇÃO ATÔMICA DE ESTOQUE (previne race condition)
        if premio.estoque is not None:
            # Usar decrement atômico com verificação de estoque > 0
            try:
                await self.db.premio.update(
                    where={
                        "id": premio_id,
                        "estoque": {"gt": 0}  # Só atualiza se estoque > 0
                    },
                    data={"estoque": {"decrement": 1}}
                )
            except Exception as e:
                # Se falhar, provavelmente estoque já zerou
                security_logger.error(
                    f"Falha ao decrementar estoque (race condition?) - "
                    f"Premio: {premio_id}, Erro: {str(e)}"
                )
                # Reverter débito de pontos se necessário
                return {
                    "success": False,
                    "error": "Estoque esgotado durante o processamento"
                }
        
        return {
            "success": True,
            "resgate_id": resgate.id,
            "premio": self._serialize(premio),
            "pontos_usados": custo,
            "novo_saldo": result.get("saldo_posterior", saldo_atual - custo),
            "transacao_id": result.get("transacao_id")
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
                "data_resgate": r.createdAt.isoformat() if r.createdAt else None
            }
            for r in resgates
        ]
    
    async def confirmar_entrega(self, resgate_id: int, funcionario_id: int) -> Dict[str, Any]:
        """Confirmar entrega de prêmio resgatado"""
        resgate = await self.db.resgatepremio.find_unique(where={"id": resgate_id})
        if not resgate:
            return {"success": False, "error": "Resgate não encontrado"}
        
        if resgate.status == "ENTREGUE":
            return {"success": False, "error": "Prêmio já foi entregue"}
        
        await self.db.resgatepremio.update(
            where={"id": resgate_id},
            data={
                "status": "ENTREGUE",
                "funcionarioEntregaId": funcionario_id
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
