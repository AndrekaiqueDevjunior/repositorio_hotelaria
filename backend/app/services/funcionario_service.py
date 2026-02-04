from typing import Dict, Any, List
from datetime import datetime
from fastapi import HTTPException
from app.schemas.funcionario_schema import FuncionarioCreate, FuncionarioUpdate, FuncionarioResponse
from app.repositories.funcionario_repo import FuncionarioRepository
from app.core.security import hash_password, verify_password, create_access_token


class FuncionarioService:
    def __init__(self, funcionario_repo: FuncionarioRepository):
        self.funcionario_repo = funcionario_repo
    
    async def list_all(self) -> List[Dict[str, Any]]:
        """Listar todos os funcionários"""
        return await self.funcionario_repo.list_all()
    
    async def create(self, dados: FuncionarioCreate) -> Dict[str, Any]:
        """Criar novo funcionário"""
        try:
            return await self.funcionario_repo.create(dados)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_by_id(self, funcionario_id: int) -> Dict[str, Any]:
        """Obter funcionário por ID"""
        try:
            return await self.funcionario_repo.get_by_id(funcionario_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Funcionário com ID {funcionario_id} não encontrado"
            )
    
    async def get_by_email(self, email: str) -> Dict[str, Any]:
        """Obter funcionário por email"""
        try:
            return await self.funcionario_repo.get_by_email(email)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Funcionário com email {email} não encontrado"
            )
    
    async def update(self, funcionario_id: int, dados: FuncionarioUpdate) -> Dict[str, Any]:
        """Atualizar funcionário"""
        try:
            return await self.funcionario_repo.update(funcionario_id, dados)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Funcionário com ID {funcionario_id} não encontrado para atualização"
            )
    
    async def delete(self, funcionario_id: int) -> Dict[str, Any]:
        """Deletar funcionário (soft delete - inativa)"""
        try:
            return await self.funcionario_repo.delete(funcionario_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Funcionário com ID {funcionario_id} não encontrado para inativação"
            )
    
    async def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """Autenticar funcionário e gerar token"""
        try:
            funcionario = await self.funcionario_repo.get_by_email(email)
            
            # Verificar se funcionário está ativo
            if funcionario["status"] != "ATIVO":
                raise HTTPException(status_code=401, detail="Funcionário inativo")
            
            # Verificar senha - obter senha hash do banco
            from app.core.database import get_db
            db = get_db()
            funcionario_db = await db.funcionario.find_unique(where={"email": email})
            
            if not funcionario_db:
                raise HTTPException(status_code=401, detail="Credenciais inválidas")
            
            # Verificar senha
            if not verify_password(password, funcionario_db.senha):
                raise HTTPException(status_code=401, detail="Credenciais inválidas")
            
            # Gerar token JWT
            token_data = {
                "sub": str(funcionario["id"]),
                "email": funcionario["email"],
                "perfil": funcionario["perfil"]
            }
            access_token = create_access_token(data=token_data)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "funcionario": {
                    "id": funcionario["id"],
                    "nome": funcionario["nome"],
                    "email": funcionario["email"],
                    "perfil": funcionario["perfil"]
                }
            }
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Erro na autenticação: {str(e)}")
    
    async def list_by_perfil(self, perfil: str) -> List[Dict[str, Any]]:
        """Listar funcionários por perfil"""
        funcionarios = await self.funcionario_repo.list_all()
        return [f for f in funcionarios if f["perfil"] == perfil]
    
    async def list_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Listar funcionários por status"""
        funcionarios = await self.funcionario_repo.list_all()
        return [f for f in funcionarios if f["status"] == status]


# Instância global para compatibilidade
_funcionario_service = None

async def get_funcionario_service() -> FuncionarioService:
    """Factory para obter instância do serviço"""
    global _funcionario_service
    if _funcionario_service is None:
        from app.core.database import get_db
        db = get_db()
        _funcionario_service = FuncionarioService(FuncionarioRepository(db))
    return _funcionario_service

# Funções de compatibilidade para migração gradual
async def listar_funcionarios():
    service = await get_funcionario_service()
    return await service.list_all()

async def criar_funcionario(dados: FuncionarioCreate):
    service = await get_funcionario_service()
    return await service.create(dados)

async def obter_funcionario(funcionario_id: int):
    service = await get_funcionario_service()
    return await service.get_by_id(funcionario_id)

async def atualizar_funcionario(funcionario_id: int, dados: FuncionarioUpdate):
    service = await get_funcionario_service()
    return await service.update(funcionario_id, dados)