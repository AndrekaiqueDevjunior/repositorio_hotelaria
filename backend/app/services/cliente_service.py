from typing import Dict, Any, List
from fastapi import HTTPException
from app.schemas.cliente_schema import ClienteCreate, ClienteResponse
from app.repositories.cliente_repo import ClienteRepository


class ClienteService:
    def __init__(self, cliente_repo: ClienteRepository):
        self.cliente_repo = cliente_repo
    
    async def list_all(
        self, 
        search: str = None, 
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Listar todos os clientes com filtros e busca"""
        return await self.cliente_repo.list_all(
            search=search, 
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def create(self, dados: ClienteCreate) -> Dict[str, Any]:
        """Criar novo cliente"""
        try:
            return await self.cliente_repo.create(dados)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_by_id(self, cliente_id: int) -> Dict[str, Any]:
        """Obter cliente por ID"""
        try:
            return await self.cliente_repo.get_by_id(cliente_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Cliente com ID {cliente_id} não encontrado"
            )
    
    async def get_by_documento(self, documento: str) -> Dict[str, Any]:
        """Obter cliente por documento"""
        try:
            return await self.cliente_repo.get_by_documento(documento)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Cliente com documento {documento} não encontrado"
            )
    
    async def update(self, cliente_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar cliente"""
        try:
            return await self.cliente_repo.update(cliente_id, data)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Cliente com ID {cliente_id} não encontrado para atualização"
            )
    
    async def delete(self, cliente_id: int) -> Dict[str, Any]:
        """Deletar cliente"""
        try:
            return await self.cliente_repo.delete(cliente_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Cliente com ID {cliente_id} não encontrado para exclusão"
            )
        except Exception as e:
            error_msg = str(e)
            if "Foreign key constraint" in error_msg or "ForeignKeyViolation" in error_msg:
                raise HTTPException(
                    status_code=409,
                    detail=f"Não é possível excluir o cliente {cliente_id} pois existem reservas ou pagamentos associados. Exclua os registros relacionados primeiro."
                )
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao excluir cliente: {error_msg}"
            )


# Instância global para compatibilidade (será removida quando migrarmos totalmente)
_cliente_service = None

async def get_cliente_service() -> ClienteService:
    """Factory para obter instância do serviço"""
    global _cliente_service
    if _cliente_service is None:
        from app.core.database import get_db
        db = get_db()
        _cliente_service = ClienteService(ClienteRepository(db))
    return _cliente_service

# Funções de compatibilidade para migração gradual
async def listar_clientes():
    service = await get_cliente_service()
    return await service.list_all()

async def criar_cliente(dados: ClienteCreate):
    service = await get_cliente_service()
    return await service.create(dados)

async def obter_cliente(cliente_id: int):
    service = await get_cliente_service()
    return await service.get_by_id(cliente_id)