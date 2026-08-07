from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.usuario import PerfilUsuario


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=60)
    senha: str = Field(..., min_length=1)
    perfil_solicitado: PerfilUsuario = Field(...)
    senha_admin: Optional[str] = Field(None)


class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    login: str = Field(..., min_length=3, max_length=60)
    senha: str = Field(..., min_length=4)
    perfil: PerfilUsuario = Field(...)
    ativo: bool = Field(True)


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=120)
    login: Optional[str] = Field(None, min_length=3, max_length=60)
    senha: Optional[str] = Field(None, min_length=4)
    perfil: Optional[PerfilUsuario] = Field(None)
    ativo: Optional[bool] = Field(None)


class UsuarioOut(BaseModel):
    id: int
    nome: str
    login: str
    perfil: PerfilUsuario

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
