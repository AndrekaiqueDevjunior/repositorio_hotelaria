"""
Repositório de Prêmios RP (Reais Pontos)
Gerencia o catálogo de prêmios e resgates
"""

from typing import List, Optional, Dict
from app.models.premios_rp import PremioRP, ResgatePremio
from app.core.enums import CategoriaPremio
from decimal import Decimal

class PremiosRPRepository:
    """Repositório para gerenciar prêmios RP"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_premio(self, premio_data: Dict) -> PremioRP:
        """Criar novo prêmio no catálogo"""
        premio = PremioRP(
            nome=premio_data["nome"],
            descricao=premio_data.get("descricao"),
            categoria=premio_data["categoria"],
            preco_em_rp=premio_data["preco_em_rp"],
            imagem_url=premio_data.get("imagem_url"),
            estoque=premio_data.get("estoque", 0),
            valor_estimado=premio_data.get("valor_estimado"),
            ativo=premio_data.get("ativo", True)
        )
        
        self.db.add(premio)
        self.db.commit()
        self.db.refresh(premio)
        return premio
    
    async def list_premios(self, ativo: Optional[bool] = None, categoria: Optional[CategoriaPremio] = None) -> List[PremioRP]:
        """Listar prêmios disponíveis"""
        query = self.db.query(PremioRP)
        
        if ativo is not None:
            query = query.filter(PremioRP.ativo == ativo)
        
        if categoria is not None:
            query = query.filter(PremioRP.categoria == categoria)
        
        return query.order_by(PremioRP.nome).all()
    
    async def get_premio_by_id(self, premio_id: int) -> Optional[PremioRP]:
        """Obter prêmio por ID"""
        return self.db.query(PremioRP).filter(PremioRP.id == premio_id).first()
    
    async def update_premio(self, premio_id: int, update_data: Dict) -> Optional[PremioRP]:
        """Atualizar dados do prêmio"""
        premio = await self.get_premio_by_id(premio_id)
        if not premio:
            return None
        
        for key, value in update_data.items():
            if hasattr(premio, key):
                setattr(premio, key, value)
        
        self.db.commit()
        self.db.refresh(premio)
        return premio
    
    async def delete_premio(self, premio_id: int) -> bool:
        """Desativar prêmio (soft delete)"""
        premio = await self.get_premio_by_id(premio_id)
        if not premio:
            return False
        
        premio.ativo = False
        self.db.commit()
        return True
    
    async def criar_resgate(self, resgate_data: Dict) -> ResgatePremio:
        """Criar nova solicitação de resgate"""
        resgate = ResgatePremio(
            premio_id=resgate_data["premio_id"],
            cliente_id=resgate_data["cliente_id"],
            pontos_utilizados=resgate_data["pontos_utilizados"],
            observacoes=resgate_data.get("observacoes"),
            criado_por_usuario_id=resgate_data.get("criado_por_usuario_id")
        )
        
        self.db.add(resgate)
        self.db.commit()
        self.db.refresh(resgate)
        return resgate
    
    async def list_resgates_cliente(self, cliente_id: int, status: Optional[str] = None) -> List[ResgatePremio]:
        """Listar resgates de um cliente"""
        query = self.db.query(ResgatePremio).filter(ResgatePremio.cliente_id == cliente_id)
        
        if status:
            query = query.filter(ResgatePremio.status_resgate == status)
        
        return query.order_by(ResgatePremio.data_solicitacao.desc()).all()
    
    async def list_resgates(self, status: Optional[str] = None) -> List[ResgatePremio]:
        """Listar todos os resgates"""
        query = self.db.query(ResgatePremio)
        
        if status:
            query = query.filter(ResgatePremio.status_resgate == status)
        
        return query.order_by(ResgatePremio.data_solicitacao.desc()).all()
    
    async def atualizar_status_resgate(self, resgate_id: int, novo_status: str, usuario_id: Optional[int] = None) -> Optional[ResgatePremio]:
        """Atualizar status de um resgate"""
        resgate = self.db.query(ResgatePremio).filter(ResgatePremio.id == resgate_id).first()
        if not resgate:
            return None
        
        resgate.status_resgate = novo_status
        
        if novo_status == "APROVADO":
            from app.utils.datetime_utils import now_utc
            resgate.data_aprovacao = now_utc()
        elif novo_status == "ENTREGUE":
            from app.utils.datetime_utils import now_utc
            resgate.data_entrega = now_utc()
        
        self.db.commit()
        self.db.refresh(resgate)
        return resgate
    
    async def get_estatisticas_premios(self) -> Dict:
        """Obter estatísticas dos prêmios"""
        total_premios = self.db.query(PremioRP).filter(PremioRP.ativo == True).count()
        total_resgates = self.db.query(ResgatePremio).count()
        
        # Resgates por status
        resgates_pendentes = self.db.query(ResgatePremio).filter(ResgatePremio.status_resgate == "PENDENTE").count()
        resgates_aprovados = self.db.query(ResgatePremio).filter(ResgatePremio.status_resgate == "APROVADO").count()
        resgates_entregues = self.db.query(ResgatePremio).filter(ResgatePremio.status_resgate == "ENTREGUE").count()
        
        return {
            "total_premios_disponiveis": total_premios,
            "total_resgates": total_resgates,
            "resgates_pendentes": resgates_pendentes,
            "resgates_aprovados": resgates_aprovados,
            "resgates_entregues": resgates_entregues
        }
