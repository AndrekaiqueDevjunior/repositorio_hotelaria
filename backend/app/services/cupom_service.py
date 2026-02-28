from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.repositories.cupom_repo import CupomRepository


class CupomService:
    def __init__(self, cupom_repo: CupomRepository):
        self.cupom_repo = cupom_repo

    async def list_all(self, apenas_ativos: bool = False) -> List[Dict[str, Any]]:
        return await self.cupom_repo.list_all(apenas_ativos=apenas_ativos)

    async def get_by_id(self, cupom_id: int) -> Dict[str, Any]:
        cupom = await self.cupom_repo.get_by_id(cupom_id)
        if not cupom:
            raise HTTPException(status_code=404, detail="Cupom não encontrado")
        return cupom

    async def create(self, data: Dict[str, Any], criado_por: Optional[int] = None) -> Dict[str, Any]:
        try:
            return await self.cupom_repo.create(data, criado_por=criado_por)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    async def update(self, cupom_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cupom = await self.cupom_repo.update(cupom_id, data)
            if not cupom:
                raise HTTPException(status_code=404, detail="Cupom não encontrado")
            return cupom
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    async def set_ativo(self, cupom_id: int, ativo: bool) -> Dict[str, Any]:
        try:
            cupom = await self.cupom_repo.set_ativo(cupom_id, ativo)
            if not cupom:
                raise HTTPException(status_code=404, detail="Cupom não encontrado")
            return cupom
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    async def delete(self, cupom_id: int) -> Dict[str, Any]:
        ok = await self.cupom_repo.delete(cupom_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Cupom não encontrado")
        return {"success": True, "message": "Cupom desativado com sucesso"}

    async def validar(self, **kwargs) -> Dict[str, Any]:
        try:
            return await self.cupom_repo.validar_cupom(**kwargs)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Erro ao validar cupom: {str(exc)}")

    async def aplicar_em_reserva(self, reserva_id: int, codigo: str) -> Dict[str, Any]:
        try:
            return await self.cupom_repo.aplicar_cupom_reserva(reserva_id, codigo)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Erro ao aplicar cupom: {str(exc)}")

    async def remover_da_reserva(self, reserva_id: int) -> Dict[str, Any]:
        try:
            return await self.cupom_repo.remover_cupom_reserva(reserva_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Erro ao remover cupom: {str(exc)}")

    async def obter_cupom_reserva(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        return await self.cupom_repo.obter_cupom_reserva(reserva_id)
