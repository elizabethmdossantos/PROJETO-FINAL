from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.venda import FormaPagamento, StatusVenda


class ItemVendaEntrada(BaseModel):
    codigo_produto: str = Field(..., min_length=1, max_length=30)
    quantidade: int = Field(..., gt=0)


class VendaCriar(BaseModel):
    forma_pagamento: FormaPagamento
    itens: List[ItemVendaEntrada]

    @field_validator("itens")
    @classmethod
    def precisa_de_ao_menos_um_item(cls, itens):
        if not itens:
            raise ValueError("A venda precisa ter ao menos um item.")
        return itens


class ItemVendaOut(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class ItemVendaDetalhado(ItemVendaOut):
    codigo_produto: str
    nome_produto: str


class VendaOut(BaseModel):
    id: int
    caixa_id: int
    usuario_id: int
    forma_pagamento: FormaPagamento
    status: StatusVenda
    valor_total: Decimal
    criado_em: datetime
    itens: List[ItemVendaOut] = []

    model_config = ConfigDict(from_attributes=True)


class VendaDetalhada(BaseModel):
    id: int
    caixa_id: int
    usuario_id: int
    nome_operador: str
    forma_pagamento: FormaPagamento
    status: StatusVenda
    valor_total: Decimal
    criado_em: datetime
    itens: List[ItemVendaDetalhado] = []

    model_config = ConfigDict(from_attributes=True)
