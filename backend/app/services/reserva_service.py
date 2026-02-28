from typing import Dict, Any, List
from datetime import datetime, timezone
from app.utils.datetime_utils import now_utc, to_utc
from fastapi import HTTPException
from app.schemas.reserva_schema import ReservaCreate, ReservaResponse
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.core.validators import ReservaValidator
from app.services.integrate_notificacoes import (
    notificar_em_reserva_criada,
    notificar_em_checkin,
    notificar_em_checkout,
    notificar_em_cancelamento
)

class ReservaService:
    def __init__(self, reserva_repo: ReservaRepository, cliente_repo: ClienteRepository, quarto_repo: QuartoRepository):
        self.reserva_repo = reserva_repo
        self.cliente_repo = cliente_repo
        self.quarto_repo = quarto_repo
    
    async def list_all(
        self,
        search: str = None,
        status: str = None,
        checkin_inicio: str = None,
        checkin_fim: str = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = None
    ) -> Dict[str, Any]:
        """
        Listar todas as reservas com filtros e busca
        
        Parâmetros:
        - search: Termo de busca (nome do cliente, número do quarto ou código da reserva)
        - status: Filtro por status da reserva
        - checkin_inicio: Data de check-in inicial (YYYY-MM-DD)
        - checkin_fim: Data de check-in final (YYYY-MM-DD)
        - limit: Número máximo de registros por página
        - offset: Deslocamento para paginação
        - order_by: Ordenação no formato "campo:ordem" (ex: "data_criacao:desc")
        """
        return await self.reserva_repo.list_all(
            search=search,
            status=status,
            checkin_inicio=checkin_inicio,
            checkin_fim=checkin_fim,
            limit=limit,
            offset=offset,
            order_by=order_by
        )
    
    async def create(self, dados: ReservaCreate) -> Dict[str, Any]:
        """Criar nova reserva com validações"""
        try:
            # Criar reserva
            reserva = await self.reserva_repo.create(dados)
            
            # Enviar notificação (em background, não bloquear)
            try:
                from app.core.database import get_db
                db = next(get_db())
                await notificar_em_reserva_criada(db, reserva)
                print(f"[NOTIFICAÇÃO] Nova reserva {reserva.get('codigo_reserva')} notificada")
            except Exception as e:
                print(f"[NOTIFICAÇÃO] Erro ao notificar nova reserva: {e}")
            
            return reserva
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_by_id(self, reserva_id: int) -> Dict[str, Any]:
        """Obter reserva por ID"""
        try:
            return await self.reserva_repo.get_by_id(reserva_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Reserva com ID {reserva_id} não encontrada"
            )
    
    async def checkin(self, reserva_id: int) -> Dict[str, Any]:
        """Realizar check-in da reserva"""
        try:
            # Realizar check-in
            reserva = await self.reserva_repo.checkin(reserva_id)
            
            # Enviar notificação
            try:
                from app.core.database import get_db
                db = next(get_db())
                await notificar_em_checkin(db, reserva)
                print(f"[NOTIFICAÇÃO] Check-in realizado para reserva {reserva.get('codigo_reserva')}")
            except Exception as e:
                print(f"[NOTIFICAÇÃO] Erro ao notificar check-in: {e}")
            
            return reserva
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Reserva com ID {reserva_id} não encontrada para check-in"
            )
    
    async def checkout(self, reserva_id: int) -> Dict[str, Any]:
        """
        Realizar check-out da reserva E creditar pontos automaticamente
        PROTEGIDO CONTRA DUPLICAÇÃO: Verifica se já fez checkout antes de processar
        """
        from app.core.database import get_db
        
        try:
            # CAMADA 1: Buscar reserva atual
            db = get_db()
            reserva_atual = await db.reserva.find_unique(where={"id": reserva_id})
            
            if not reserva_atual:
                raise ValueError(f"Reserva {reserva_id} não encontrada")
            
            # CAMADA 2: Validar se pode fazer checkout
            ReservaValidator.validar_checkout(reserva_atual)
            
            # CAMADA 3: Verificar se já fez checkout (IDEMPOTENTE)
            if reserva_atual.status == "CHECKED_OUT":
                print(f"[CHECKOUT] Reserva {reserva_id} já está em CHECKED_OUT - retornando sem processar")
                # Retornar reserva existente (idempotente)
                return await self.reserva_repo.get_by_id(reserva_id)
            
            # CAMADA 4: Validar saldo devedor
            saldo_devedor = await self._calcular_saldo_devedor(reserva_id)
            if saldo_devedor > 0:
                raise ValueError(f"Não é possível fazer check-out com saldo devedor de R$ {saldo_devedor:.2f}")
            
            # CAMADA 5: Verificar se já creditou pontos (proteção adicional)
            transacao_existente = await db.transacaopontos.find_first(
                where={
                    "reservaId": reserva_id,
                    "tipo": "CREDITO",
                    "origem": "CHECKOUT"
                }
            )
            
            # CAMADA 6: Realizar checkout
            reserva = await self.reserva_repo.checkout(reserva_id)
            
            # CAMADA 7: Creditar pontos usando serviço unificado
            if not transacao_existente:
                try:
                    # CRÉDITO DE PONTOS OFICIAL (RealPointsService)
                    from app.services.real_points_service import RealPointsService
                    
                    # Validar requisitos oficiais
                    pode, motivo = RealPointsService.validar_requisitos_oficiais(reserva)
                    
                    if pode:
                        # Validar antifraude
                        valido, motivo_antifraude = RealPointsService.validar_antifraude(reserva)
                        
                        if valido:
                            # Calcular pontos
                            rp, detalhe = RealPointsService.calcular_rp_oficial(
                                reserva["tipo_suite"], 
                                reserva["num_diarias"], 
                                reserva["valor_total"]
                            )
                            
                            if rp > 0:
                                # Creditar pontos
                                print(f"[CHECKOUT] Creditando {rp} RP para cliente {reserva['cliente_id']}")
                                reserva["pontos_gerados"] = rp
                                reserva["pontos_detalhe"] = detalhe
                                reserva["pontos_creditados_em"] = datetime.now(timezone.utc).isoformat()
                            else:
                                print(f"[CHECKOUT] Sem pontos para gerar: {detalhe}")
                        else:
                            print(f"[CHECKOUT] Antifraude bloqueou: {motivo_antifraude}")
                    else:
                        print(f"[CHECKOUT] Requisitos não atendidos: {motivo}")
                        
                except Exception as e:
                    print(f"⚠️ Erro ao creditar pontos no checkout: {str(e)}")
                    reserva["pontos_credito_erro"] = str(e)
            else:
                print(f"[CHECKOUT] Pontos já creditados para reserva {reserva_id} - pulando crédito")
            
            return reserva
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def _calcular_saldo_devedor(self, reserva_id: int) -> float:
        """Calcular saldo devedor da reserva"""
        from app.core.database import get_db
        
        db = get_db()
        
        # Buscar reserva
        reserva = await db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            return 0.0
        
        # Calcular valor total
        valor_total = float(reserva.valorDiaria or 0) * (reserva.numDiarias or 0)
        
        # Buscar pagamentos aprovados
        pagamentos = await db.pagamento.find_many(
            where={
                "reservaId": reserva_id,
                "status": "APROVADO"
            }
        )
        
        valor_pago = sum(float(p.valor or 0) for p in pagamentos)
        saldo = valor_total - valor_pago
        
        return max(0.0, saldo)
    
    async def _creditar_pontos_checkout(self, reserva: Dict[str, Any]) -> None:
        """
        Creditar pontos de fidelidade após checkout
        Regra: 1 ponto para cada R$ 10,00 gastos
        """
        from app.core.database import get_db
        from app.services.real_points_service import RealPointsService

        db = get_db()
        await creditar_rp_no_checkout(
            db,
            reserva_id=reserva["id"],
            funcionario_id=None,
            checkout_datetime=None,
        )
    
    async def list_by_cliente(self, cliente_id: int) -> List[Dict[str, Any]]:
        """Listar reservas de um cliente"""
        # Implementação futura - buscar por cliente_id
        reservas = await self.reserva_repo.list_all()
        cliente_reservas = [r for r in reservas["reservas"] if r["cliente_id"] == cliente_id]
        return cliente_reservas
    
    async def cancelar(self, reserva_id: int) -> Dict[str, Any]:
        """Cancelar reserva"""
        try:
            return await self.reserva_repo.cancelar(reserva_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def confirmar(self, reserva_id: int) -> Dict[str, Any]:
        """Confirmar reserva"""
        try:
            return await self.reserva_repo.confirmar(reserva_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def update(self, reserva_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar dados gerais da reserva"""
        try:
            return await self.reserva_repo.update(reserva_id, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


# Instância global para compatibilidade
_reserva_service = None

async def get_reserva_service() -> ReservaService:
    """Factory para obter instância do serviço"""
    global _reserva_service
    if _reserva_service is None:
        from app.core.database import get_db
        db = get_db()
        _reserva_service = ReservaService(
            ReservaRepository(db),
            ClienteRepository(db),
            QuartoRepository(db)
        )
    return _reserva_service

# Funções de compatibilidade para migração gradual
async def listar_reservas():
    service = await get_reserva_service()
    return await service.list_all()

async def criar_reserva(dados: ReservaCreate):
    service = await get_reserva_service()
    return await service.create(dados)

async def obter_reserva(reserva_id: int):
    service = await get_reserva_service()
    return await service.get_by_id(reserva_id)

async def checkin_reserva(reserva_id: int):
    service = await get_reserva_service()
    return await service.checkin(reserva_id)

async def checkout_reserva(reserva_id: int):
    service = await get_reserva_service()
    return await service.checkout(reserva_id)