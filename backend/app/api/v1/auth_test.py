"""
Endpoint de teste para autenticação - Diagnóstico e correção
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_db
from app.utils.hashing import hash_password, verify_password
from app.core.security import create_access_token
import hashlib

router = APIRouter(prefix="/auth-test", tags=["auth-test"])

class LoginTest(BaseModel):
    email: str
    password: str

class AdminCreateTest(BaseModel):
    email: str = "admin@hotelreal.com.br"
    password: str = "admin123"
    nome: str = "Administrador"

@router.post("/test-login")
async def test_login(login_data: LoginTest):
    """Testar login com diagnóstico detalhado"""
    try:
        db = get_db()
        
        # Buscar funcionário
        funcionario = await db.funcionario.find_unique(
            where={"email": login_data.email}
        )
        
        if not funcionario:
            return {
                "success": False,
                "error": "Funcionário não encontrado",
                "email_searched": login_data.email
            }
        
        # Verificar senha
        senha_hash_banco = funcionario.senha
        senha_fornecida = login_data.password
        senha_hash_calculada = hash_password(senha_fornecida)
        
        # Diagnóstico detalhado
        resultado = {
            "success": False,
            "funcionario_encontrado": True,
            "funcionario_id": funcionario.id,
            "funcionario_nome": funcionario.nome,
            "funcionario_status": funcionario.status,
            "senha_hash_banco": senha_hash_banco[:20] + "...",  # Primeiros 20 chars
            "senha_hash_calculada": senha_hash_calculada[:20] + "...",
            "senhas_coincidem": senha_hash_banco == senha_hash_calculada,
            "verify_password_result": verify_password(senha_fornecida, senha_hash_banco)
        }
        
        # Verificar se funcionário está ativo
        if funcionario.status != "ATIVO":
            resultado["error"] = "Funcionário inativo"
            return resultado
        
        # Verificar senha
        if not verify_password(senha_fornecida, senha_hash_banco):
            resultado["error"] = "Senha incorreta"
            return resultado
        
        # Gerar token
        token_data = {
            "sub": str(funcionario.id),
            "email": funcionario.email,
            "perfil": funcionario.perfil
        }
        access_token = create_access_token(data=token_data)
        
        resultado.update({
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "funcionario": {
                "id": funcionario.id,
                "nome": funcionario.nome,
                "email": funcionario.email,
                "perfil": funcionario.perfil
            }
        })
        
        return resultado
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro interno: {str(e)}",
            "exception_type": type(e).__name__
        }

@router.post("/create-admin-test")
async def create_admin_test(admin_data: AdminCreateTest):
    """Criar/recriar administrador para teste"""
    try:
        db = get_db()
        
        # Verificar se já existe
        existing = await db.funcionario.find_unique(
            where={"email": admin_data.email}
        )
        
        if existing:
            # Deletar existente
            await db.funcionario.delete(where={"id": existing.id})
        
        # Criar novo admin
        senha_hash = hash_password(admin_data.password)
        
        admin = await db.funcionario.create(
            data={
                "nome": admin_data.nome,
                "email": admin_data.email,
                "senha": senha_hash,
                "perfil": "ADMIN",
                "status": "ATIVO"
            }
        )
        
        return {
            "success": True,
            "message": "Admin criado com sucesso",
            "admin": {
                "id": admin.id,
                "nome": admin.nome,
                "email": admin.email,
                "perfil": admin.perfil,
                "status": admin.status
            },
            "senha_hash": senha_hash[:20] + "...",
            "senha_original": admin_data.password
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao criar admin: {str(e)}",
            "exception_type": type(e).__name__
        }

@router.get("/hash-test/{password}")
async def hash_test(password: str):
    """Testar função de hash"""
    try:
        hash1 = hash_password(password)
        hash2 = hashlib.sha256(password.encode()).hexdigest()
        
        return {
            "password": password,
            "hash_utils": hash1,
            "hash_direct": hash2,
            "hashes_match": hash1 == hash2,
            "verify_test": verify_password(password, hash1)
        }
    except Exception as e:
        return {
            "error": str(e),
            "exception_type": type(e).__name__
        }

@router.get("/list-funcionarios")
async def list_funcionarios():
    """Listar todos os funcionários para debug"""
    try:
        db = get_db()
        funcionarios = await db.funcionario.find_many()
        
        return {
            "total": len(funcionarios),
            "funcionarios": [
                {
                    "id": f.id,
                    "nome": f.nome,
                    "email": f.email,
                    "perfil": f.perfil,
                    "status": f.status,
                    "senha_hash": f.senha[:20] + "..." if f.senha else "None"
                }
                for f in funcionarios
            ]
        }
    except Exception as e:
        return {
            "error": str(e),
            "exception_type": type(e).__name__
        }
