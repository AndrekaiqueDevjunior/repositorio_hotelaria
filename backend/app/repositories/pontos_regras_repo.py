from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from prisma import Client


def _date_to_db_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


class PontosRegrasRepository:
    def __init__(self, db: Client):
        self.db = db

    def _normalize_write_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data or {})

        if "suiteTipo" in payload and payload["suiteTipo"] is not None:
            payload["suiteTipo"] = str(payload["suiteTipo"]).upper().strip()

        if "dataInicio" in payload and isinstance(payload["dataInicio"], date) and not isinstance(payload["dataInicio"], datetime):
            payload["dataInicio"] = _date_to_db_datetime(payload["dataInicio"])

        if "dataInicio" in payload and isinstance(payload["dataInicio"], datetime) and payload["dataInicio"].tzinfo is None:
            payload["dataInicio"] = payload["dataInicio"].replace(tzinfo=timezone.utc)

        if "dataFim" in payload and isinstance(payload["dataFim"], date) and not isinstance(payload["dataFim"], datetime):
            payload["dataFim"] = _date_to_db_datetime(payload["dataFim"])

        if "dataFim" in payload and isinstance(payload["dataFim"], datetime) and payload["dataFim"].tzinfo is None:
            payload["dataFim"] = payload["dataFim"].replace(tzinfo=timezone.utc)

        return payload

    async def list_all(self, ativo: Optional[bool] = None) -> List[Dict[str, Any]]:
        where = {}
        if ativo is not None:
            where["ativo"] = ativo

        regras = await self.db.pontosregra.find_many(
            where=where if where else None,
            order={"dataInicio": "desc"},
        )

        return [self._serialize(r) for r in regras]

    async def get_by_id(self, regra_id: int) -> Optional[Dict[str, Any]]:
        regra = await self.db.pontosregra.find_unique(where={"id": regra_id})
        return self._serialize(regra) if regra else None

    async def verificar_sobreposicao(
        self,
        suite_tipo: str,
        data_inicio: date,
        data_fim: date,
        ignore_id: Optional[int] = None,
    ) -> bool:
        suite_tipo_norm = (suite_tipo or "").upper().strip()
        di = _date_to_db_datetime(data_inicio)
        df = _date_to_db_datetime(data_fim)

        where: Dict[str, Any] = {
            "suiteTipo": suite_tipo_norm,
            "ativo": True,
            "AND": [
                {"dataInicio": {"lte": df}},
                {"dataFim": {"gte": di}},
            ],
        }

        if ignore_id is not None:
            where["NOT"] = {"id": ignore_id}

        existente = await self.db.pontosregra.find_first(where=where)
        return bool(existente)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        regra = await self.db.pontosregra.create(data=self._normalize_write_data(data))
        return self._serialize(regra)

    async def update(self, regra_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            regra = await self.db.pontosregra.update(where={"id": regra_id}, data=self._normalize_write_data(data))
            return self._serialize(regra)
        except Exception:
            return None

    async def soft_delete(self, regra_id: int) -> bool:
        try:
            await self.db.pontosregra.update(where={"id": regra_id}, data={"ativo": False})
            return True
        except Exception:
            return False

    def _serialize(self, regra) -> Dict[str, Any]:
        return {
            "id": regra.id,
            "suite_tipo": regra.suiteTipo,
            "diarias_base": regra.diariasBase,
            "rp_por_base": regra.rpPorBase,
            "temporada": getattr(regra, "temporada", None),
            "data_inicio": regra.dataInicio.date() if isinstance(regra.dataInicio, datetime) else regra.dataInicio,
            "data_fim": regra.dataFim.date() if isinstance(regra.dataFim, datetime) else regra.dataFim,
            "ativo": regra.ativo,
        }
