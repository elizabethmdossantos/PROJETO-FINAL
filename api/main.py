"""
Regras de negócio do sistema.
Cria os enpoints.
Ativa a segurança, verificando se o token de acesso é válido.
Processa os dados.
"""
from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
# imporação de dados do outro arquivo (schemas)
from schemas import (
    ProdutoCadastro, ProdutoResposta, MovimentacaoResposta, 
    ResumoDiarioResposta, FinanceiroResposta, UsuarioLogin, TokenResposta
)
# inicialização do FastAPI
app = FastAPI(
    title="API de Gestão Comercial",
    description="Núcleo do Sistema - Autenticação e Mock de Dados",
    version="1.0.0"
)
# segurança HTTPBearer (padrão do token JWT)
security = HTTPBearer()

# SEGURANÇA / CONTROLE DE ACESSO
# Função de Dependência para proteger as rotas da API
def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Simula validação do token
    if token != "token-valido-admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"usuario": "admin"}

# ENDPOINT DE AUTENTICAÇÃO
@app.post("/api/auth/login", response_model=TokenResposta)
def login(dados: UsuarioLogin):
    # Mock de usuário e senha temporários
    if dados.usuario == "admin" and dados.senha == "admin123":
        return {"access_token": "token-valido-admin", "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário ou senha incorretos."
    )

# MOCKS DE DADOS
MOCK_PRODUTOS = [
    {"nome": "Teclado Mecânico", "quantidade": 15},
    {"nome": "Mouse Gamer", "quantidade": 22}
]

MOCK_MOVIMENTACOES = [
    {"produto_nome": "Teclado Mecânico", "quantidade_entrada": 20, "quantidade_saida": 5},
    {"produto_nome": "Mouse Gamer", "quantidade_entrada": 30, "quantidade_saida": 8}
]

# ENDPOINTS PROTEGIDOS

@app.get("/api/resumo-diario", response_model=ResumoDiarioResposta)
def obter_resumo_diario(usuario_logado: dict = Depends(verificar_token)):
    return {"faturamento": 1250.45, "vendas": 14, "status_caixa": "Aberto"}

@app.post("/api/produtos", status_code=status.HTTP_201_CREATED)
def cadastrar_produto(produto: ProdutoCadastro, usuario_logado: dict = Depends(verificar_token)):
    if produto.codigo == "999":
        raise HTTPException(status_code=400, detail="Já existe um produto cadastrado com este código.")
    MOCK_PRODUTOS.append({"nome": produto.nome, "quantidade": produto.quantidade})
    return {"mensagem": "Produto e movimentação cadastrados com sucesso!"}

@app.get("/api/produtos", response_model=List[ProdutoResposta])
def listar_produtos(usuario_logado: dict = Depends(verificar_token)):
    return MOCK_PRODUTOS

@app.get("/api/movimentacoes", response_model=List[MovimentacaoResposta])
def listar_movimentacoes(usuario_logado: dict = Depends(verificar_token)):
    return MOCK_MOVIMENTACOES

@app.get("/api/financeiro-resumo", response_model=FinanceiroResposta)
def obter_resumo_financeiro(usuario_logado: dict = Depends(verificar_token)):
    return {"a_receber": 4500.00, "a_pagar": 1850.30, "saldo_consolidado": 2649.70}

@app.get("/api/relatorios/exportar")
def exportar_relatorio(tipo_relatorio: str, formato: str, data_inicio: str, data_fim: str, usuario_logado: dict = Depends(verificar_token)):
    return {"status": "pronto", "tipo": tipo_relatorio, "formato": formato}


"""
# Endpoint simulado para o PDV do Gustavo registrar uma venda
@app.post("/api/vendas", status_code=status.HTTP_201_CREATED)
def registrar_venda(venda: dict, usuario_logado: dict = Depends(verificar_token)):

    # Recebe os itens vendidos no Frente de Caixa, abate as quantidades do estoque e atualiza o histórico de movimentações (saídas).

    # Exemplo de lógica que rodará aqui:
    # 1. Deduzir do MOCK_PRODUTOS a quantidade vendida
    # 2. Inserir em MOCK_MOVIMENTACOES com o tipo "venda"
    return {"status": "sucesso", "mensagem": "Venda processada e estoque atualizado!"}
"""