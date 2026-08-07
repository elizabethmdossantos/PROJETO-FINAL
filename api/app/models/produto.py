from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, func

from app.core.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), unique=True, nullable=False, index=True)
    nome = Column(String(120), nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    estoque = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, default=True, nullable=False)
    disponivel_loja = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())
