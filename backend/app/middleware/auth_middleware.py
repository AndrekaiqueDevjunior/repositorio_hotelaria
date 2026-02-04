"""
Middleware de autenticação JWT para proteger rotas
"""
from fastapi import Request, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import get_current_user, User
from typing import Optional

# Security scheme para Swagger
security = HTTPBearer()

async def get_current_active_user(
    request: Request,
    authorization: str = Header(None, alias="Authorization")
) -> User:
    """
    Dependency para obter usuário autenticado
    Aceita tanto Bearer token (header) quanto cookie
    Usar em rotas que precisam de autenticação
    """
    # Passar request e authorization para get_current_user
    # Ele vai tentar header Authorization primeiro, depois cookie
    return await get_current_user(request, authorization)

async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency para rotas que exigem perfil ADMIN
    """
    if current_user.perfil != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Acesso negado. Apenas administradores podem acessar esta rota."
        )
    return current_user

async def require_admin_or_manager(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency para rotas que exigem perfil ADMIN ou GERENTE
    """
    if current_user.perfil not in ["ADMIN", "GERENTE"]:
        raise HTTPException(
            status_code=403, 
            detail="Acesso negado. Apenas administradores ou gerentes podem acessar esta rota."
        )
    return current_user

async def require_staff(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency para rotas que exigem qualquer funcionário autenticado
    """
    # Se chegou até aqui, o usuário já está autenticado
    return current_user

# Aliases para facilitar uso
RequireAuth = Depends(get_current_active_user)
RequireAdmin = Depends(require_admin)
RequireAdminOrManager = Depends(require_admin_or_manager)
RequireStaff = Depends(require_staff)
