import enum

from sqlalchemy import (
    Column, Integer, Numeric, Enum, DateTime, ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class FormaPagamento(str, enum.Enum):
    DINHEIRO = "dinheiro"
    PIX = "pix"
    CARTAO = "cartao"
    VALE_REFEICAO = "vale_refeicao"
    # Pedido feito pelo site da "Feira Online" e pago antes da retirada.
    ONLINE = "online"


class StatusVenda(str, enum.Enum):
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)

    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    status = Column(Enum(StatusVenda), nullable=False, default=StatusVenda.CONCLUIDA)
    valor_total = Column(Numeric(10, 2), nullable=False, default=0)

    criado_em = Column(DateTime, server_default=func.now())

    caixa = relationship("Caixa", back_populates="vendas")
    usuario = relationship("Usuario")
    itens = relationship(
        "ItemVenda", back_populates="venda", cascade="all, delete-orphan"
    )


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("vendas.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)

    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto")
