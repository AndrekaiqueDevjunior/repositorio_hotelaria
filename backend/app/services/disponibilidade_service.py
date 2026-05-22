"""
Servico de disponibilidade de quartos.

Regra canonica: uma reserva bloqueia um quarto quando ha intersecao real
entre periodos: existente.checkin < novo.checkout e existente.checkout > novo.checkin.
Assim, checkout e novo check-in no mesmo instante sao permitidos.
"""
from typing import Any, Dict, List
from datetime import datetime
from prisma import Client


STATUS_RESERVA_BLOQUEIA_DISPONIBILIDADE = [
    "PENDENTE",
    "PENDENTE_PAGAMENTO",
    "AGUARDANDO_PAGAMENTO",
    "AGUARDANDO_COMPROVANTE",
    "EM_ANALISE",
    "CONFIRMADA",
    "PAGA_APROVADA",
    "CHECKIN_LIBERADO",
    "CHECKIN_REALIZADO",
    "HOSPEDADO",
    "CHECKED_IN",
]

STATUS_QUARTO_BLOQUEIA_DISPONIBILIDADE = ["BLOQUEADO", "MANUTENCAO", "INATIVO"]


class DisponibilidadeService:
    """Servico para verificar disponibilidade de quartos."""

    def __init__(self, db: Client):
        self.db = db

    def _where_conflito(
        self,
        checkin: datetime,
        checkout: datetime,
        quarto_numero: str = None,
        quartos_numeros: List[str] = None,
        reserva_id_excluir: int = None,
    ) -> Dict[str, Any]:
        where_clause: Dict[str, Any] = {
            "statusReserva": {"in": STATUS_RESERVA_BLOQUEIA_DISPONIBILIDADE},
            "checkinPrevisto": {"lt": checkout},
            "checkoutPrevisto": {"gt": checkin},
        }

        if quarto_numero is not None:
            where_clause["quartoNumero"] = quarto_numero
        elif quartos_numeros is not None:
            where_clause["quartoNumero"] = {"in": quartos_numeros}

        if reserva_id_excluir:
            where_clause["id"] = {"not": reserva_id_excluir}

        return where_clause

    async def verificar_disponibilidade(
        self,
        quarto_numero: str,
        checkin: datetime,
        checkout: datetime,
        reserva_id_excluir: int = None,
    ) -> Dict[str, Any]:
        if checkout <= checkin:
            return {
                "disponivel": False,
                "motivo": "Data de check-out deve ser posterior ao check-in",
                "conflitos": [],
            }

        quarto = await self.db.quarto.find_unique(where={"numero": quarto_numero})
        if not quarto:
            return {
                "disponivel": False,
                "motivo": "Quarto nao encontrado",
                "conflitos": [],
            }

        if quarto.status in STATUS_QUARTO_BLOQUEIA_DISPONIBILIDADE:
            status_map = {
                "MANUTENCAO": "em manutencao",
                "BLOQUEADO": "bloqueado",
                "INATIVO": "inativo",
            }
            return {
                "disponivel": False,
                "motivo": f"Quarto esta {status_map.get(quarto.status, quarto.status.lower())}",
                "conflitos": [],
            }

        reservas_conflitantes = await self.db.reserva.find_many(
            where=self._where_conflito(
                checkin=checkin,
                checkout=checkout,
                quarto_numero=quarto_numero,
                reserva_id_excluir=reserva_id_excluir,
            ),
            include={"cliente": True},
        )

        if reservas_conflitantes:
            conflitos = [
                {
                    "reserva_id": r.id,
                    "codigo": r.codigoReserva,
                    "cliente": r.clienteNome,
                    "checkin": r.checkinPrevisto.isoformat(),
                    "checkout": r.checkoutPrevisto.isoformat(),
                    "status": r.statusReserva,
                }
                for r in reservas_conflitantes
            ]
            return {
                "disponivel": False,
                "motivo": f"Quarto ja possui {len(conflitos)} reserva(s) no periodo",
                "conflitos": conflitos,
            }

        return {
            "disponivel": True,
            "motivo": "Quarto disponivel",
            "conflitos": [],
        }

    async def listar_quartos_disponiveis(
        self,
        checkin: datetime,
        checkout: datetime,
        tipo_suite: str = None,
    ) -> List[Dict[str, Any]]:
        if checkout <= checkin:
            return []

        where_clause: Dict[str, Any] = {
            "status": {"notIn": STATUS_QUARTO_BLOQUEIA_DISPONIBILIDADE}
        }

        if tipo_suite:
            where_clause["tipoSuite"] = tipo_suite

        quartos = await self.db.quarto.find_many(where=where_clause)
        if not quartos:
            return []

        numeros_quartos = [q.numero for q in quartos]
        reservas_conflitantes = await self.db.reserva.find_many(
            where=self._where_conflito(
                checkin=checkin,
                checkout=checkout,
                quartos_numeros=numeros_quartos,
            )
        )
        quartos_ocupados = {r.quartoNumero for r in reservas_conflitantes}

        return [
            {
                "numero": quarto.numero,
                "tipo_suite": quarto.tipoSuite,
                "status": quarto.status,
                "disponivel": True,
            }
            for quarto in quartos
            if quarto.numero not in quartos_ocupados
        ]

    async def verificar_multiplos_quartos(
        self,
        checkin: datetime,
        checkout: datetime,
    ) -> Dict[str, Any]:
        quartos = await self.db.quarto.find_many()
        quartos_disponiveis = await self.listar_quartos_disponiveis(checkin, checkout)
        numeros_disponiveis = {q["numero"] for q in quartos_disponiveis}

        resultado = {
            "total_quartos": len(quartos),
            "disponiveis": len(numeros_disponiveis),
            "ocupados": len(quartos) - len(numeros_disponiveis),
            "quartos": [],
        }

        for quarto in quartos:
            disponivel = quarto.numero in numeros_disponiveis
            detalhes = (
                {"disponivel": True, "motivo": "Quarto disponivel", "conflitos": []}
                if disponivel
                else await self.verificar_disponibilidade(quarto.numero, checkin, checkout)
            )
            resultado["quartos"].append({
                "numero": quarto.numero,
                "tipo_suite": quarto.tipoSuite,
                "status_quarto": quarto.status,
                "disponivel": detalhes["disponivel"],
                "motivo": detalhes["motivo"],
                "conflitos": detalhes["conflitos"],
            })

        return resultado

    async def sugerir_quartos_alternativos(
        self,
        tipo_suite: str,
        checkin: datetime,
        checkout: datetime,
        limite: int = 5,
    ) -> List[Dict[str, Any]]:
        quartos_disponiveis = await self.listar_quartos_disponiveis(
            checkin,
            checkout,
            tipo_suite,
        )
        return quartos_disponiveis[:limite]
