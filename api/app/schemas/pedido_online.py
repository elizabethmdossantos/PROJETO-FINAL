from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.pedido_online import StatusPedidoOnline


class ItemPedidoEntrada(BaseModel):
    produto_id: int
    quantidade: int = Field(..., gt=0)


class PedidoOnlineCriar(BaseModel):
    nome_cliente: str = Field(..., min_length=2, max_length=120)
    telefone_cliente: str = Field(..., min_length=8, max_length=20)
    itens: List[ItemPedidoEntrada]

    @field_validator("itens")
    @classmethod
    def precisa_de_ao_menos_um_item(cls, itens):
        if not itens:
            raise ValueError("O pedido precisa ter ao menos um item.")
        return itens


class PedidoOnlineConsultar(BaseModel):
    numero_pedido: str
    telefone_cliente: str


class VerificarQuantidade(BaseModel):
    produto_id: int
    quantidade: int = Field(..., gt=0)


class VerificarQuantidadeResposta(BaseModel):
    disponivel: bool
    maximo_disponivel: Optional[int] = None


class ItemPedidoOut(BaseModel):
    id: int
    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class PedidoOnlineOut(BaseModel):
    id: int
    numero_pedido: str
    nome_cliente: str
    telefone_cliente: str
    status: StatusPedidoOnline

    subtotal: Decimal
    taxa_servico_percentual: Decimal
    taxa_servico_valor: Decimal
    valor_total: Decimal

    taxa_cancelamento_percentual: Optional[Decimal] = None
    taxa_cancelamento_valor: Optional[Decimal] = None
    valor_reembolsado: Optional[Decimal] = None

    criado_em: datetime
    retirado_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None

    itens: List[ItemPedidoOut] = []

    model_config = ConfigDict(from_attributes=True)
