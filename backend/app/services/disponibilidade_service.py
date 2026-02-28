"""
Serviço de Disponibilidade de Quartos
Verifica conflitos de reservas e disponibilidade
"""
from typing import List, Dict, Any
from datetime import datetime, date
from prisma import Client


class DisponibilidadeService:
    """Serviço para verificar disponibilidade de quartos"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def verificar_disponibilidade(
        self,
        quarto_numero: str,
        checkin: datetime,
        checkout: datetime,
        reserva_id_excluir: int = None
    ) -> Dict[str, Any]:
        """
        Verificar se quarto está disponível no período
        
        Args:
            quarto_numero: Número do quarto
            checkin: Data/hora de check-in
            checkout: Data/hora de check-out
            reserva_id_excluir: ID da reserva a excluir da verificação (para edição)
        
        Returns:
            {
                "disponivel": bool,
                "motivo": str,
                "conflitos": List[Dict]
            }
        """
        # Buscar quarto
        quarto = await self.db.quarto.find_unique(where={"numero": quarto_numero})
        if not quarto:
            return {
                "disponivel": False,
                "motivo": "Quarto não encontrado",
                "conflitos": []
            }
        
        # CORREÇÃO CRÍTICA: Verificar status do quarto
        # Apenas quartos LIVRE podem ser reservados
        if quarto.status != "LIVRE":
            status_map = {
                "OCUPADO": "ocupado",
                "RESERVADO": "reservado",
                "MANUTENCAO": "em manutenção",
                "BLOQUEADO": "bloqueado"
            }
            motivo = status_map.get(quarto.status, quarto.status.lower())
            return {
                "disponivel": False,
                "motivo": f"Quarto está {motivo}",
                "conflitos": []
            }
        
        # Buscar reservas que conflitam com o período
        # Conflito ocorre quando:
        # 1. Nova reserva começa durante uma reserva existente
        # 2. Nova reserva termina durante uma reserva existente
        # 3. Nova reserva engloba completamente uma reserva existente
        
        status_ativos = [
            "PENDENTE_PAGAMENTO",
            "AGUARDANDO_COMPROVANTE",
            "EM_ANALISE",
            "CONFIRMADA",
            "PAGA_REJEITADA",
            "CHECKIN_REALIZADO",
            "HOSPEDADO",
            "PENDENTE",
            "PAGA_APROVADA",
            "CHECKIN_LIBERADO",
            "AGUARDANDO_PAGAMENTO",
        ]

        where_clause = {
            "quartoNumero": quarto_numero,
            "statusReserva": {
                "in": status_ativos
            },
            "OR": [
                # Caso 1: Check-in da nova reserva está dentro de uma reserva existente
                {
                    "checkinPrevisto": {"lte": checkin},
                    "checkoutPrevisto": {"gt": checkin}
                },
                # Caso 2: Check-out da nova reserva está dentro de uma reserva existente
                {
                    "checkinPrevisto": {"lt": checkout},
                    "checkoutPrevisto": {"gte": checkout}
                },
                # Caso 3: Nova reserva engloba completamente uma reserva existente
                {
                    "checkinPrevisto": {"gte": checkin},
                    "checkoutPrevisto": {"lte": checkout}
                }
            ]
        }
        
        # Excluir a própria reserva se estiver editando
        if reserva_id_excluir:
            where_clause["id"] = {"not": reserva_id_excluir}
        
        reservas_conflitantes = await self.db.reserva.find_many(
            where=where_clause,
            include={"cliente": True}
        )
        
        if reservas_conflitantes:
            conflitos = [
                {
                    "reserva_id": r.id,
                    "codigo": r.codigoReserva,
                    "cliente": r.clienteNome,
                    "checkin": r.checkinPrevisto.isoformat(),
                    "checkout": r.checkoutPrevisto.isoformat(),
                    "status": r.statusReserva
                }
                for r in reservas_conflitantes
            ]
            
            return {
                "disponivel": False,
                "motivo": f"Quarto já possui {len(conflitos)} reserva(s) no período",
                "conflitos": conflitos
            }
        
        return {
            "disponivel": True,
            "motivo": "Quarto disponível",
            "conflitos": []
        }
    
    async def listar_quartos_disponiveis(
        self,
        checkin: datetime,
        checkout: datetime,
        tipo_suite: str = None
    ) -> List[Dict[str, Any]]:
        """
        Listar quartos disponíveis no período
        
        Args:
            checkin: Data/hora de check-in
            checkout: Data/hora de check-out
            tipo_suite: Filtrar por tipo de suíte (opcional)
        
        Returns:
            Lista de quartos disponíveis
        """
        # CORREÇÃO CRÍTICA: Buscar APENAS quartos LIVRE
        # Quartos OCUPADOS, RESERVADOS, MANUTENCAO e BLOQUEADOS não devem aparecer
        where_clause = {
            "status": "LIVRE"  # Apenas quartos livres podem ser reservados
        }
        
        if tipo_suite:
            where_clause["tipoSuite"] = tipo_suite
        
        quartos = await self.db.quarto.find_many(where=where_clause)
        
        quartos_disponiveis = []
        
        for quarto in quartos:
            resultado = await self.verificar_disponibilidade(
                quarto.numero,
                checkin,
                checkout
            )
            
            if resultado["disponivel"]:
                quartos_disponiveis.append({
                    "numero": quarto.numero,
                    "tipo_suite": quarto.tipoSuite,
                    "status": quarto.status,
                    "disponivel": True
                })
        
        return quartos_disponiveis
    
    async def verificar_multiplos_quartos(
        self,
        checkin: datetime,
        checkout: datetime
    ) -> Dict[str, Any]:
        """
        Verificar disponibilidade de todos os quartos no período
        
        Returns:
            {
                "total_quartos": int,
                "disponiveis": int,
                "ocupados": int,
                "quartos": List[Dict]
            }
        """
        quartos = await self.db.quarto.find_many()
        
        resultado = {
            "total_quartos": len(quartos),
            "disponiveis": 0,
            "ocupados": 0,
            "quartos": []
        }
        
        for quarto in quartos:
            disponibilidade = await self.verificar_disponibilidade(
                quarto.numero,
                checkin,
                checkout
            )
            
            if disponibilidade["disponivel"]:
                resultado["disponiveis"] += 1
            else:
                resultado["ocupados"] += 1
            
            resultado["quartos"].append({
                "numero": quarto.numero,
                "tipo_suite": quarto.tipoSuite,
                "status_quarto": quarto.status,
                "disponivel": disponibilidade["disponivel"],
                "motivo": disponibilidade["motivo"],
                "conflitos": disponibilidade["conflitos"]
            })
        
        return resultado
    
    async def sugerir_quartos_alternativos(
        self,
        tipo_suite: str,
        checkin: datetime,
        checkout: datetime,
        limite: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Sugerir quartos alternativos do mesmo tipo que estão disponíveis
        
        Args:
            tipo_suite: Tipo de suíte desejado
            checkin: Data/hora de check-in
            checkout: Data/hora de check-out
            limite: Número máximo de sugestões
        
        Returns:
            Lista de quartos alternativos disponíveis
        """
        quartos_disponiveis = await self.listar_quartos_disponiveis(
            checkin,
            checkout,
            tipo_suite
        )
        
        return quartos_disponiveis[:limite]
