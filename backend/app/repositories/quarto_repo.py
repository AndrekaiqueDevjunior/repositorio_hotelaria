from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from prisma import Client
from app.schemas.quarto_schema import QuartoCreate, QuartoUpdate, QuartoResponse, StatusQuarto, TipoSuite
from app.utils.datetime_utils import now_utc


class QuartoRepository:
    def __init__(self, db: Client):
        self.db = db
    
    async def list_all(
        self,
        search: str = None,
        status: str = None,
        tipo_suite: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Listar todos os quartos com filtros e busca"""
        where_conditions = {}
        
        # Filtro de busca (número ou andar)
        if search:
            where_conditions["numero"] = {"contains": search, "mode": "insensitive"}
        
        # Filtro de status
        if status:
            where_conditions["status"] = status
        
        # Filtro de tipo de suíte
        if tipo_suite:
            where_conditions["tipoSuite"] = tipo_suite
        
        # Buscar total de registros (para paginação)
        total = await self.db.quarto.count(where=where_conditions if where_conditions else None)
        
        # Buscar registros com paginação
        registros = await self.db.quarto.find_many(
            where=where_conditions if where_conditions else None,
            order={"numero": "asc"},
            skip=offset,
            take=limit
        )
        
        return {
            "quartos": [self._serialize_quarto(q) for q in registros],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def create(self, quarto: QuartoCreate) -> Dict[str, Any]:
        """Criar novo quarto"""
        existente = await self.db.quarto.find_unique(where={"numero": quarto.numero})
        if existente:
            raise ValueError("Quarto já existe")
        
        novo_quarto = await self.db.quarto.create(
            data={
                "numero": quarto.numero,
                "tipoSuite": quarto.tipo_suite,
                "status": quarto.status
            }
        )
        
        return self._serialize_quarto(novo_quarto)
    
    async def get_by_numero(self, numero: str) -> Dict[str, Any]:
        """Obter quarto por número"""
        quarto = await self.db.quarto.find_unique(where={"numero": numero})
        if not quarto:
            raise ValueError("Quarto não encontrado")
        return self._serialize_quarto(quarto)
    
    async def update(self, numero: str, quarto: QuartoUpdate) -> Dict[str, Any]:
        """Atualizar quarto"""
        quarto_existente = await self.db.quarto.find_unique(where={"numero": numero})
        if not quarto_existente:
            raise ValueError("Quarto não encontrado")
        
        update_data = {}
        if quarto.numero is not None:
            update_data["numero"] = quarto.numero
        if quarto.tipo_suite is not None:
            update_data["tipoSuite"] = quarto.tipo_suite
        if quarto.status is not None:
            update_data["status"] = quarto.status
        
        await self.db.quarto.update(
            where={"numero": numero},
            data=update_data
        )
        
        updated_quarto = await self.db.quarto.find_unique(where={"numero": numero})
        return self._serialize_quarto(updated_quarto)
    
    async def update_status(self, numero: str, status: StatusQuarto) -> Dict[str, Any]:
        """Atualizar apenas o status do quarto"""
        quarto = await self.db.quarto.find_unique(where={"numero": numero})
        if not quarto:
            raise ValueError("Quarto não encontrado")
        
        await self.db.quarto.update(
            where={"numero": numero},
            data={"status": status}
        )
        
        updated_quarto = await self.db.quarto.find_unique(where={"numero": numero})
        return self._serialize_quarto(updated_quarto)
    
    async def delete(self, numero: str) -> Dict[str, Any]:
        """Deletar quarto"""
        quarto = await self.db.quarto.find_unique(where={"numero": numero})
        if not quarto:
            raise ValueError("Quarto não encontrado")
        
        # Verificar se o quarto tem reservas ativas
        reservas_ativas = await self.db.reserva.find_many(
            where={
                "quartoNumero": numero,
                "statusReserva": {"in": ["PENDENTE", "CONFIRMADA", "HOSPEDADO", "CHECKIN_REALIZADO"]}
            }
        )
        
        if reservas_ativas:
            raise ValueError(
                f"Não é possível excluir o quarto {numero}. Ele possui {len(reservas_ativas)} reserva(s) ativa(s). "
                "Cancele ou finalize as reservas antes de excluir."
            )
        
        # Se não houver restrições, deleta o quarto
        await self.db.quarto.delete(where={"numero": numero})
        
        return {
            "success": True,
            "message": "Quarto excluído com sucesso",
            "numero": numero
        }
    
    def _serialize_quarto(self, quarto) -> Dict[str, Any]:
        """Serializar quarto para response"""
        return {
            "id": quarto.id,
            "numero": quarto.numero,
            "tipo_suite": quarto.tipoSuite,
            "status": quarto.status,
            "created_at": quarto.createdAt.isoformat() if quarto.createdAt else None
        }
    
    async def get_historico(self, numero: str, limit: int = 50) -> Dict[str, Any]:
        """Obter histórico de ocupação do quarto"""
        quarto = await self.db.quarto.find_unique(where={"numero": numero})
        if not quarto:
            raise ValueError("Quarto não encontrado")
        
        # Buscar todas as reservas do quarto (ordenadas da mais recente para a mais antiga)
        reservas = await self.db.reserva.find_many(
            where={"quartoNumero": numero},
            include={
                "cliente": True,
                "pagamentos": True
            },
            order={"checkinPrevisto": "desc"},
            take=limit
        )
        
        # Calcular estatísticas
        total_reservas = len(reservas)
        reservas_concluidas = len([r for r in reservas if r.statusReserva == "CHECKED_OUT"])
        reservas_canceladas = len([r for r in reservas if r.statusReserva == "CANCELADO"])
        reservas_ativas = len([r for r in reservas if r.statusReserva in ["PENDENTE", "CONFIRMADA", "HOSPEDADO", "CHECKIN_REALIZADO"]])
        
        # Calcular taxa de ocupação (últimos 90 dias)
        data_limite = now_utc() - timedelta(days=90)
        reservas_recentes = [r for r in reservas if r.checkinPrevisto >= data_limite]
        
        dias_ocupados = 0
        for reserva in reservas_recentes:
            if reserva.checkoutPrevisto and reserva.checkinPrevisto:
                delta = reserva.checkoutPrevisto - reserva.checkinPrevisto
                dias_ocupados += delta.days
        
        taxa_ocupacao = round((dias_ocupados / 90) * 100, 1) if dias_ocupados > 0 else 0
        
        return {
            "quarto": self._serialize_quarto(quarto),
            "estatisticas": {
                "total_reservas": total_reservas,
                "concluidas": reservas_concluidas,
                "canceladas": reservas_canceladas,
                "ativas": reservas_ativas,
                "taxa_ocupacao_90d": taxa_ocupacao
            },
            "historico": [self._serialize_reserva_historico(r) for r in reservas]
        }
    
    async def get_reserva_atual(self, numero: str) -> Dict[str, Any]:
        """Obter reserva atual/ativa do quarto"""
        quarto = await self.db.quarto.find_unique(where={"numero": numero})
        if not quarto:
            raise ValueError("Quarto não encontrado")
        
        # Buscar reserva ativa (CHECKIN ou CONFIRMADA para hoje/futuro)
        reserva_ativa = await self.db.reserva.find_first(
            where={
                "quartoNumero": numero,
                "statusReserva": {"in": ["HOSPEDADO", "CHECKIN_REALIZADO", "CONFIRMADA", "PENDENTE"]}
            },
            include={
                "cliente": True,
                "pagamentos": True
            },
            order={"checkinPrevisto": "asc"}
        )
        
        if not reserva_ativa:
            return {
                "quarto": self._serialize_quarto(quarto),
                "reserva_atual": None,
                "status": "LIVRE"
            }
        
        return {
            "quarto": self._serialize_quarto(quarto),
            "reserva_atual": self._serialize_reserva_historico(reserva_ativa),
            "status": "OCUPADO" if reserva_ativa.statusReserva in ["HOSPEDADO", "CHECKIN_REALIZADO"] else "RESERVADO"
        }
    
    def _serialize_reserva_historico(self, reserva) -> Dict[str, Any]:
        """Serializar reserva para histórico"""
        return {
            "id": reserva.id,
            "cliente": {
                "id": reserva.cliente.id,
                "nome": reserva.cliente.nomeCompleto,
                "email": reserva.cliente.email
            } if reserva.cliente else None,
            "data_checkin": reserva.checkinPrevisto.isoformat() if reserva.checkinPrevisto else None,
            "data_checkout": reserva.checkoutPrevisto.isoformat() if reserva.checkoutPrevisto else None,
            "status": reserva.statusReserva,
            "valor_total": float(reserva.valorDiaria) * reserva.numDiarias if reserva.valorDiaria and reserva.numDiarias else 0,
            "pagamentos": len(reserva.pagamentos) if reserva.pagamentos else 0,
            "created_at": reserva.createdAt.isoformat() if reserva.createdAt else None
        }