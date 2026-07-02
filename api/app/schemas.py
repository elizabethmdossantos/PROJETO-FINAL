"""
Definir as regras de contrato e validar os dados.
Nível: Pydantic v2 (FastAPI)
"""
from pydantic import BaseModel, Field
from typing import List

# =========================================================================
# 1. USUÁRIOS & AUTENTICAÇÃO (Cadastro, Login e RBAC)
# =========================================================================

class UsuarioCadastro(BaseModel):
    """Schema para criação de novos usuários com definição de perfil (RBAC)"""
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário único")
    senha: str = Field(..., min_length=6, description="Senha com no mínimo 6 caracteres")
    perfil: str = Field(..., description="Perfil de acesso: 'administrador' ou 'vendedor'")


class UsuarioLogin(BaseModel):
    """Schema de entrada para receber as credenciais enviadas pela tela de login"""
    usuario: str
    senha: str


class TokenResposta(BaseModel):
    """Padrão de resposta gerado após um login bem-sucedido"""
    access_token: str
    token_type: str
    perfil: str  # Ajuda o Flask a saber qual menu e permissões renderizar na tela (RBAC)


# =========================================================================
# 2. PRODUTOS (Validação e Resposta)
# =========================================================================

class ProdutoCadastro(BaseModel):
    """Schema de validação para o formulário de cadastro de produtos"""
    nome: str = Field(..., min_length=1, description="Nome do produto")
    codigo: str = Field(..., min_length=1, description="Código identificador único")
    preco_custo: float = Field(..., gt=0, description="Preço de custo deve ser maior que zero")
    preco_venda: float = Field(..., gt=0, description="Preço de venda deve ser maior que zero")
    categoria: str = Field(..., min_length=1, description="Categoria do produto")
    quantidade: int = Field(..., ge=0, description="Quantidade inicial não pode ser negativa")


class ProdutoResposta(BaseModel):
    """Define exatamente quais campos serão visíveis ao listar produtos"""
    id: int
    codigo: str
    nome: str
    preco_venda: float
    quantidade: int

    class Config:
        from_attributes = True  # Permite que a FastAPI converta instâncias do SQLAlchemy direto para JSON


# =========================================================================
# 3. GESTÃO COMERCIAL / PDV
# =========================================================================

class ItemVendaEntrada(BaseModel):
    """Representa um item individual sendo vendido no carrinho do PDV"""
    produto_id: int = Field(..., description="ID do produto vendido")
    quantidade: int = Field(..., gt=0, description="Quantidade deve ser no mínimo 1")


class VendaCadastro(BaseModel):
    """Contrato recebido do JavaScript/Flask quando uma venda é finalizada"""
    itens: List[ItemVendaEntrada] = Field(..., min_length=1, description="Lista de itens da venda")


# =========================================================================
# 4. MONITORAMENTO & FINANCEIRO (Outputs)
# =========================================================================

class MovimentacaoResposta(BaseModel):
    """Alimenta o histórico de entradas e saídas de mercadorias na tela de estoque"""
    produto_name: str  # Renomeado na API para bater com o join m.produto.nome
    quantidade_entrada: int
    quantidade_saida: int


class ResumoDiarioResposta(BaseModel):
    """Preenche os cards informativos principais do Dashboard"""
    faturamento: float
    vendas: int
    status_caixa: str


class FinanceiroResposta(BaseModel):
    """Estrutura os dados financeiros consolidados na tela administrativa"""
    a_receber: float
    a_pagar: float
    saldo_consolidado: float