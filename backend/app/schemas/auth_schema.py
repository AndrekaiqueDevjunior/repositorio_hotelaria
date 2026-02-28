from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponseUser(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    funcionario: LoginResponseUser


class AdminPasswordVerifyRequest(BaseModel):
    password: str