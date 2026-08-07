import enum

from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, func

from app.core.database import Base


class PerfilUsuario(str, enum.Enum):
    ADMIN = "admin"
    CAIXA = "caixa"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    login = Column(String(60), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilUsuario), nullable=False, default=PerfilUsuario.CAIXA)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())
