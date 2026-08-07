import enum

from sqlalchemy import (
    Column, Integer, Numeric, Enum, DateTime, String, ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class StatusCaixa(str, enum.Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"


class Caixa(Base):
    __tablename__ = "caixas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)

    status = Column(Enum(StatusCaixa), nullable=False, default=StatusCaixa.ABERTO)

    valor_abertura = Column(Numeric(10, 2), nullable=False, default=0)
    valor_fechamento = Column(Numeric(10, 2), nullable=True)

    aberto_em = Column(DateTime, server_default=func.now())
    fechado_em = Column(DateTime, nullable=True)

    observacoes = Column(String(255), nullable=True)

    usuario = relationship("Usuario")
    vendas = relationship("Venda", back_populates="caixa")
