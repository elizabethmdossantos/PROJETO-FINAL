"""
Definir as regras de contrato e validar os dados.
"""
from pydantic import BaseModel, Field

# VALIDAÇÃO E ENTRADA DE DADOS
class ProdutoCadastro(BaseModel):
    # schema de validação para o formulário do cadastro de produtos
    # '...' significa campo obrigatório
    # 'min_length=1' impede textos vazios
    nome: str = Field(..., min_length=1, description="Nome do produto")
    codigo: str = Field(..., min_length=1, description="Código identificador único")
    # 'gt=0' (greater than) garante que os preços obrigatoriamente sejam maiores que zero
    preco_custo: float = Field(..., gt=0, description="Preço de custo deve ser maior que zero")
    preco_venda: float = Field(..., gt=0, description="Preço de venda deve ser maior que zero")
    categoria: str = Field(..., min_length=1, description="Categoria do produto")
    # 'ge=0' (greater or equal) permite estoque zerado, mas não valores negativos
    quantidade: int = Field(..., ge=0, description="Quantidade inicial não pode ser negativa")

class UsuarioLogin(BaseModel):
    # Schema de entrada para receber as credenciais enviadas pela tela de login
    usuario: str
    senha: str

# FORMATAÇÃO DE SAIDA DE DADOS
class ProdutoResposta(BaseModel):
    """
    Define exatamente quais campos serão visíveis ao listar produtos.
    Filtra informações sensíveis (como preço de custo) para a tela de estoque.
    """
    nome: str
    quantidade: int

class MovimentacaoResposta(BaseModel):
    """
    Contrato de dados estruturado para enviar o histórico de entradas e saídas
    de mercadorias que alimenta a tabela da página de estoque.
    """
    produto_nome: str
    quantidade_entrada: int
    quantidade_saida: int

class ResumoDiarioResposta(BaseModel):
    """
    Mapeia os dados que a API entrega para preencher os três cards informativos 
    principais do painel inicial (Dashboard).
    """
    faturamento: float
    vendas: int
    status_caixa: str

class FinanceiroResposta(BaseModel):
    """
    Estrutura a resposta dos dados de faturamento consolidado, contas a pagar
    e a receber para a tela de gestão financeira.
    """
    a_receber: float
    a_pagar: float
    saldo_consolidado: float

class TokenResposta(BaseModel):
    """
    Padrão de resposta gerado após um login bem-sucedido, devolvendo o Token JWT
    necessário para que o Flask consiga acessar as rotas protegidas.
    """
    access_token: str
    token_type: str