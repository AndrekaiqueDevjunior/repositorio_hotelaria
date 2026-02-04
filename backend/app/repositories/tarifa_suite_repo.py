from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from prisma import Client


def _date_to_db_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


class TarifaSuiteRepository:
    def __init__(self, db: Client):
        self.db = db

    def _normalize_write_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data or {})

        # Map snake_case to Prisma camelCase field names
        field_mapping = {
            'suite_tipo': 'suiteTipo',
            'temporada': 'temporada', 
            'data_inicio': 'dataInicio',
            'data_fim': 'dataFim',
            'preco_diaria': 'precoDiaria',
            'ativo': 'ativo'
        }
        
        # Apply field mapping
        for snake_field, camel_field in field_mapping.items():
            if snake_field in payload:
                payload[camel_field] = payload.pop(snake_field)

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

    async def list_all(
        self,
        ativo: Optional[bool] = None,
        suite_tipo: Optional[str] = None,
        data: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        where: Dict[str, Any] = {}

        if ativo is not None:
            where["ativo"] = ativo

        if suite_tipo:
            where["suiteTipo"] = str(suite_tipo).upper().strip()

        if data:
            data_ref = _date_to_db_datetime(data)
            where["dataInicio"] = {"lte": data_ref}
            where["dataFim"] = {"gte": data_ref}

        tarifas = await self.db.tarifasuite.find_many(
            where=where if where else None,
            order={"dataInicio": "desc"},
        )

        return [self._serialize(t) for t in tarifas]

    async def get_by_id(self, tarifa_id: int) -> Optional[Dict[str, Any]]:
        tarifa = await self.db.tarifasuite.find_unique(where={"id": tarifa_id})
        return self._serialize(tarifa) if tarifa else None

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

        existente = await self.db.tarifasuite.find_first(where=where)
        return bool(existente)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        tarifa = await self.db.tarifasuite.create(data=self._normalize_write_data(data))
        return self._serialize(tarifa)

    async def update(self, tarifa_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            tarifa = await self.db.tarifasuite.update(
                where={"id": tarifa_id},
                data=self._normalize_write_data(data),
            )
            return self._serialize(tarifa)
        except Exception:
            return None

    async def soft_delete(self, tarifa_id: int) -> bool:
        try:
            await self.db.tarifasuite.update(where={"id": tarifa_id}, data={"ativo": False})
            return True
        except Exception:
            return False

    async def get_tarifa_ativa(self, suite_tipo: str, data_ref: date) -> Optional[Dict[str, Any]]:
        if not suite_tipo or not data_ref:
            return None

        suite_tipo_norm = str(suite_tipo).upper().strip()
        data_dt = _date_to_db_datetime(data_ref)

        tarifa = await self.db.tarifasuite.find_first(
            where={
                "suiteTipo": suite_tipo_norm,
                "ativo": True,
                "dataInicio": {"lte": data_dt},
                "dataFim": {"gte": data_dt},
            },
            order={"dataInicio": "desc"},
        )

        return self._serialize(tarifa) if tarifa else None

    def _serialize(self, tarifa) -> Dict[str, Any]:
        if not tarifa:
            return {}
        
        # Convert Prisma object to dict and clean enum values
        data = {
            "id": tarifa.id,
            "suite_tipo": tarifa.suiteTipo.replace("TIPOSUITE.", "") if "TIPOSUITE." in tarifa.suiteTipo else tarifa.suiteTipo,
            "temporada": tarifa.temporada,
            "data_inicio": tarifa.dataInicio.date() if hasattr(tarifa.dataInicio, 'date') else tarifa.dataInicio,
            "data_fim": tarifa.dataFim.date() if hasattr(tarifa.dataFim, 'date') else tarifa.dataFim,
            "preco_diaria": float(tarifa.precoDiaria),
            "ativo": tarifa.ativo,
        }
        return data
