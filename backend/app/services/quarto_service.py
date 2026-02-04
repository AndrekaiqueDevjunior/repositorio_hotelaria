from typing import Dict, Any, List
from datetime import datetime
from fastapi import HTTPException
from app.schemas.quarto_schema import QuartoCreate, QuartoUpdate, QuartoResponse, StatusQuarto, TipoSuite
from app.repositories.quarto_repo import QuartoRepository


class QuartoService:
    def __init__(self, quarto_repo: QuartoRepository):
        self.quarto_repo = quarto_repo
    
    async def list_all(
        self,
        search: str = None,
        status: str = None,
        tipo_suite: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Listar todos os quartos com filtros e busca"""
        return await self.quarto_repo.list_all(
            search=search,
            status=status,
            tipo_suite=tipo_suite,
            limit=limit,
            offset=offset
        )
    
    async def create(self, dados: QuartoCreate) -> Dict[str, Any]:
        """Criar novo quarto"""
        try:
            return await self.quarto_repo.create(dados)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_by_numero(self, numero: str) -> Dict[str, Any]:
        """Obter quarto por número"""
        try:
            return await self.quarto_repo.get_by_numero(numero)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Quarto {numero} não encontrado"
            )
    
    async def update(self, numero: str, dados: QuartoUpdate) -> Dict[str, Any]:
        """Atualizar quarto"""
        try:
            return await self.quarto_repo.update(numero, dados)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Quarto {numero} não encontrado para atualização"
            )
    
    async def update_status(self, numero: str, status: StatusQuarto) -> Dict[str, Any]:
        """Atualizar apenas o status do quarto"""
        try:
            return await self.quarto_repo.update_status(numero, status)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Quarto {numero} não encontrado para atualização de status"
            )
    
    async def delete(self, numero: str) -> Dict[str, Any]:
        """Deletar quarto"""
        try:
            return await self.quarto_repo.delete(numero)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Quarto {numero} não encontrado para deleção"
            )
            raise HTTPException(status_code=400, detail=str(e))
    
    async def list_by_status(self, status: StatusQuarto) -> List[Dict[str, Any]]:
        """Listar quartos por status"""
        result = await self.quarto_repo.list_all()
        quartos = result.get("quartos", [])
        return [q for q in quartos if q.get("status") == status]
    
    async def list_by_tipo(self, tipo: TipoSuite) -> List[Dict[str, Any]]:
        """Listar quartos por tipo"""
        result = await self.quarto_repo.list_all()
        quartos = result.get("quartos", [])
        return [q for q in quartos if q.get("tipo_suite") == tipo]
    
    async def get_disponiveis(self) -> List[Dict[str, Any]]:
        """Listar quartos disponíveis"""
        result = await self.quarto_repo.list_all()
        quartos = result.get("quartos", [])
        return [q for q in quartos if q.get("status") == StatusQuarto.LIVRE]
    
    async def get_historico(self, numero: str, limit: int = 50) -> Dict[str, Any]:
        """Obter histórico de ocupação do quarto"""
        try:
            return await self.quarto_repo.get_historico(numero, limit)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    async def get_reserva_atual(self, numero: str) -> Dict[str, Any]:
        """Obter reserva atual/ativa do quarto"""
        try:
            return await self.quarto_repo.get_reserva_atual(numero)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))


# Instância global para compatibilidade
_quarto_service = None

async def get_quarto_service() -> QuartoService:
    """Factory para obter instância do serviço"""
    global _quarto_service
    if _quarto_service is None:
        from app.core.database import get_db
        db = get_db()
        _quarto_service = QuartoService(QuartoRepository(db))
    return _quarto_service

# Funções de compatibilidade para migração gradual
async def listar_quartos():
    service = await get_quarto_service()
    return await service.list_all()

async def criar_quarto(dados: QuartoCreate):
    service = await get_quarto_service()
    return await service.create(dados)

async def obter_quarto(numero: str):
    service = await get_quarto_service()
    return await service.get_by_numero(numero)

async def atualizar_quarto(numero: str, dados: QuartoUpdate):
    service = await get_quarto_service()
    return await service.update(numero, dados)