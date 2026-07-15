from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.caixa import StatusCaixa


class CaixaAbrir(BaseModel):
    valor_abertura: Decimal = Field(..., ge=0)
    observacoes: Optional[str] = Field(None, max_length=255)


class CaixaFechar(BaseModel):
    valor_fechamento: Decimal = Field(..., ge=0)
    observacoes: Optional[str] = Field(None, max_length=255)


class CaixaOut(BaseModel):
    id: int
    usuario_id: int
    status: StatusCaixa
    valor_abertura: Decimal
    valor_fechamento: Optional[Decimal] = None
    aberto_em: datetime
    fechado_em: Optional[datetime] = None
    observacoes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CaixaResumo(CaixaOut):
    total_vendas: Decimal = Decimal("0")
    quantidade_vendas: int = 0
    total_pix: Decimal = Decimal("0")
    total_cartao: Decimal = Decimal("0")
    total_vale_refeicao: Decimal = Decimal("0")
