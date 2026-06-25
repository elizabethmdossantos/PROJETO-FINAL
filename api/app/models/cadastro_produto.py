from pydantic import BaseModel, Field

class ProdutoCadastro(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    codigo: str = Field(..., min_length=1, max_length=50)
    preco_custo: float = Field(..., ge=0.00)
    preco_venda: float = Field(..., ge=0.00)
    categoria: str = Field(..., min_length=2, max_length=50)
    quantidade: int = Field(..., ge=0)