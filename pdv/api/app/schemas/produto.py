from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProdutoBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=30)
    nome: str = Field(..., min_length=1, max_length=120)
    preco: Decimal = Field(..., gt=0)
    estoque: int = Field(0, ge=0)


class ProdutoCriar(ProdutoBase):
    pass


class ProdutoAtualizar(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=120)
    preco: Optional[Decimal] = Field(None, gt=0)
    estoque: Optional[int] = Field(None, ge=0)
    ativo: Optional[bool] = None


class ProdutoOut(ProdutoBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)
