import enum

from sqlalchemy import (
    Column, Integer, Numeric, Enum, DateTime, String, ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class StatusPedidoOnline(str, enum.Enum):
    AGUARDANDO_RETIRADA = "aguardando_retirada"
    RETIRADO = "retirado"
    CANCELADO = "cancelado"


class FormaPagamentoOnline(str, enum.Enum):
    PIX = "pix"
    CARTAO = "cartao"


# Percentuais praticados pela loja para o serviço de "feira pronta":
# TAXA_SERVICO é cobrada sobre o subtotal dos produtos (o funcionário monta a
# feira). TAXA_CANCELAMENTO incide sobre o valor final (produtos + serviço)
# caso o cliente desista depois de pago.
TAXA_SERVICO_PERCENTUAL = 8
TAXA_CANCELAMENTO_PERCENTUAL = 15


class PedidoOnline(Base):
    __tablename__ = "pedidos_online"

    id = Column(Integer, primary_key=True, index=True)
    numero_pedido = Column(String(20), unique=True, nullable=False, index=True)

    nome_cliente = Column(String(120), nullable=False)
    telefone_cliente = Column(String(20), nullable=False)

    forma_pagamento = Column(
        Enum(FormaPagamentoOnline), nullable=False, default=FormaPagamentoOnline.PIX
    )

    status = Column(
        Enum(StatusPedidoOnline),
        nullable=False,
        default=StatusPedidoOnline.AGUARDANDO_RETIRADA,
    )

    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    taxa_servico_percentual = Column(Numeric(5, 2), nullable=False, default=TAXA_SERVICO_PERCENTUAL)
    taxa_servico_valor = Column(Numeric(10, 2), nullable=False, default=0)
    valor_total = Column(Numeric(10, 2), nullable=False, default=0)

    taxa_cancelamento_percentual = Column(Numeric(5, 2), nullable=True)
    taxa_cancelamento_valor = Column(Numeric(10, 2), nullable=True)
    valor_reembolsado = Column(Numeric(10, 2), nullable=True)

    venda_id = Column(Integer, ForeignKey("vendas.id"), nullable=True, index=True)

    criado_em = Column(DateTime, server_default=func.now())
    retirado_em = Column(DateTime, nullable=True)
    cancelado_em = Column(DateTime, nullable=True)

    itens = relationship(
        "ItemPedidoOnline", back_populates="pedido", cascade="all, delete-orphan"
    )
    venda = relationship("Venda")


class ItemPedidoOnline(Base):
    __tablename__ = "itens_pedido_online"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos_online.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)

    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("PedidoOnline", back_populates="itens")
    produto = relationship("Produto")
