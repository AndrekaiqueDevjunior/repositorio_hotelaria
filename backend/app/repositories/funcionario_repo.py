from typing import Optional, List, Dict, Any
from datetime import datetime
from prisma import Client
from app.schemas.funcionario_schema import FuncionarioCreate, FuncionarioUpdate, FuncionarioResponse
from app.utils.hashing import hash_password


class FuncionarioRepository:
    def __init__(self, db: Client):
        self.db = db
    
    async def list_all(self) -> List[Dict[str, Any]]:
        """Listar todos os funcionários"""
        registros = await self.db.funcionario.find_many(order={"id": "asc"})
        return [self._serialize_funcionario(f) for f in registros]
    
    async def create(self, funcionario: FuncionarioCreate) -> Dict[str, Any]:
        """Criar novo funcionário"""
        existente = await self.db.funcionario.find_unique(where={"email": funcionario.email})
        if existente:
            raise ValueError("Funcionário já existe com este email")
        
        hashed_password = hash_password(funcionario.senha)
        
        novo_funcionario = await self.db.funcionario.create(
            data={
                "nome": funcionario.nome,
                "email": funcionario.email,
                "perfil": funcionario.perfil,
                "status": funcionario.status,
                "senha": hashed_password
            }
        )
        
        return self._serialize_funcionario(novo_funcionario)
    
    async def get_by_id(self, funcionario_id: int) -> Dict[str, Any]:
        """Obter funcionário por ID"""
        funcionario = await self.db.funcionario.find_unique(where={"id": funcionario_id})
        if not funcionario:
            raise ValueError("Funcionário não encontrado")
        return self._serialize_funcionario(funcionario)
    
    async def get_by_email(self, email: str) -> Dict[str, Any]:
        """Obter funcionário por email"""
        funcionario = await self.db.funcionario.find_unique(where={"email": email})
        if not funcionario:
            raise ValueError("Funcionário não encontrado")
        return self._serialize_funcionario(funcionario)
    
    async def update(self, funcionario_id: int, funcionario: FuncionarioUpdate) -> Dict[str, Any]:
        """Atualizar funcionário"""
        funcionario_existente = await self.db.funcionario.find_unique(where={"id": funcionario_id})
        if not funcionario_existente:
            raise ValueError("Funcionário não encontrado")
        
        update_data = {}
        if funcionario.nome is not None:
            update_data["nome"] = funcionario.nome
        if funcionario.email is not None:
            update_data["email"] = funcionario.email
        if funcionario.perfil is not None:
            update_data["perfil"] = funcionario.perfil
        if funcionario.status is not None:
            update_data["status"] = funcionario.status
        if funcionario.senha is not None:
            update_data["senha"] = hash_password(funcionario.senha)
        
        await self.db.funcionario.update(
            where={"id": funcionario_id},
            data=update_data
        )
        
        updated_funcionario = await self.db.funcionario.find_unique(where={"id": funcionario_id})
        return self._serialize_funcionario(updated_funcionario)
    
    async def delete(self, funcionario_id: int) -> Dict[str, Any]:
        """Deletar funcionário (soft delete - inativa ao invés de excluir)"""
        funcionario = await self.db.funcionario.find_unique(where={"id": funcionario_id})
        if not funcionario:
            raise ValueError("Funcionário não encontrado")
        
        # Soft delete - apenas inativa o funcionário
        await self.db.funcionario.update(
            where={"id": funcionario_id},
            data={"status": "INATIVO"}
        )
        
        return {
            "success": True,
            "message": "Funcionário inativado com sucesso",
            "funcionario_id": funcionario_id
        }
    
    def _serialize_funcionario(self, funcionario) -> Dict[str, Any]:
        """Serializar funcionário para response"""
        return {
            "id": funcionario.id,
            "nome": funcionario.nome,
            "email": funcionario.email,
            "perfil": funcionario.perfil,
            "status": funcionario.status,
            "fotoUrl": getattr(funcionario, "fotoUrl", None),
            "created_at": funcionario.createdAt.isoformat() if funcionario.createdAt else None,
            "updated_at": funcionario.updatedAt.isoformat() if funcionario.updatedAt else None,
        }