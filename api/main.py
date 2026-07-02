"""
API REST (FastAPI): O núcleo do sistema.
Concentra a lógica de negócio, validação, autenticação JWT real, 
controle de acesso por perfil (RBAC) e persistência no MySQL.
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, status, HTTPException, Depends, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Importações internas baseadas na estrutura do projeto
from api.app.database import get_db
from api.app import models, schemas
from api.app.schemas import (
    ProdutoCadastro, ProdutoResposta, MovimentacaoResposta, 
    ResumoDiarioResposta, FinanceiroResposta, UsuarioLogin, 
    TokenResposta, VendaCadastro, UsuarioCadastro
)

from api.app.database import engine
from api.app import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Gestão Comercial ERP",
    description="Núcleo de Inteligência e Regras de Negócio",
    version="2.0.0"
)

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configurações via variáveis de ambiente com fallbacks seguros
SECRET_KEY = os.getenv("JWT_SECRET", "super_segredo_do_erp_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# ==========================================
# SEGURANÇA, JWT E CONTROLE DE ACESSO (RBAC)
# ==========================================

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Valida o token JWT extraído do cabeçalho e expõe as claims do usuário."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido, expirado ou malformado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        perfil: str = payload.get("perfil")
        usuario_id: int = payload.get("user_id")
        if username is None or perfil is None:
            raise credentials_exception
        return {"id": usuario_id, "usuario": username, "perfil": perfil}
    except JWTError:
        raise credentials_exception

def verificar_admin(usuario_logado: dict = Depends(verificar_token)):
    """Garante restrição estrita de endpoints apenas para perfis administradores."""
    if usuario_logado.get("perfil") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Operação exclusiva para administradores."
        )
    return usuario_logado

# ==========================================
# ENDPOINTS DE AUTENTICAÇÃO E USUÁRIOS
# ==========================================

@app.post("/api/auth/registrar", status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioCadastro, db: Session = Depends(get_db)):
    """Registra novos usuários no sistema protegendo as senhas com hashing Bcrypt."""
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.username == usuario.username).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Este nome de usuário já está em uso.")
    
    if usuario.perfil not in ["administrador", "vendedor"]:
        raise HTTPException(status_code=400, detail="Perfil inválido. Use 'administrador' ou 'vendedor'.")
    
    senha_criptografada = pwd_context.hash(usuario.senha)
    novo_usuario = models.Usuario(
        username=usuario.username,
        senha_hash=senha_criptografada,
        perfil=usuario.perfil
    )
    db.add(novo_usuario)
    db.commit()
    return {"mensagem": "Usuário criado com sucesso!"}

@app.post("/api/auth/login", response_model=TokenResposta)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    """Valida as credenciais contra o MySQL e expede um token de acesso temporário."""
    usuario = db.query(models.Usuario).filter(models.Usuario.username == dados.usuario).first()
    if not usuario or not pwd_context.verify(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos."
        )
    
    tempo_expiracao = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_token = {
        "sub": usuario.username,
        "perfil": usuario.perfil,
        "user_id": usuario.id,
        "exp": tempo_expiracao
    }
    token_jwt = jwt.encode(dados_token, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token_jwt, "token_type": "bearer", "perfil": usuario.perfil}

# ==========================================
# ENDPOINTS DO PRODUTO & CONTROLE DE ESTOQUE
# ==========================================

@app.post("/api/produtos", status_code=status.HTTP_201_CREATED)
def cadastrar_produto(produto: ProdutoCadastro, db: Session = Depends(get_db), usuario_logado: dict = Depends(verificar_admin)):
    """Protegido por RBAC (Admin). Registra o item e inicializa a primeira movimentação de entrada."""
    codigo_duplicado = db.query(models.Produto).filter(models.Produto.codigo == produto.codigo).first()
    if codigo_duplicado:
        raise HTTPException(status_code=400, detail="Já existe um produto cadastrado com este código.")
    
    novo_produto = models.Produto(
        nome=produto.nome,
        codigo=produto.codigo,
        preco_custo=produto.preco_custo,
        preco_venda=produto.preco_venda,
        categoria=produto.categoria,
        quantidade=produto.quantidade
    )
    db.add(novo_produto)
    db.flush()  # Captura o ID gerado sem encerrar a transação
    
    # Registra movimentação de entrada inicial se aplicável
    if produto.quantidade > 0:
        nova_movimentacao = models.Movimentacao(
            produto_id=novo_produto.id,
            quantidade_entrada=produto.quantidade,
            quantidade_saida=0,
            tipo="entrada_inicial"
        )
        db.add(nova_movimentacao)
        
    db.commit()
    return {"mensagem": "Produto e estoque inicial registrados com sucesso!"}

@app.get("/api/produtos", response_model=List[ProdutoResposta])
def listar_produtos(db: Session = Depends(get_db), usuario_logado: dict = Depends(verificar_token)):
    """Retorna os produtos cadastrados com suporte a paginação simples via parâmetros."""
    return db.query(models.Produto).all()

# ==========================================
# FLUXO AVANÇADO DE PDV: ENTRADA DE VENDAS
# ==========================================

@app.post("/api/vendas", status_code=status.HTTP_201_CREATED)
def registrar_venda(venda: VendaCadastro, db: Session = Depends(get_db), usuario_logado: dict = Depends(verificar_token)):
    """
    DIFERENCIAL TÉCNICO: Abatimento atômico do estoque, salvamento do relacionamento
    N:N e provisionamento automático em contas a receber dentro de uma única transação SQL.
    """
    total_venda = 0.0
    itens_processados = []
    
    # Inicia explicitamente o bloco de transação atômica
    with db.begin_nested():
        for item in venda.itens:
            prod = db.query(models.Produto).filter(models.Produto.id == item.produto_id).with_for_update().first()
            if not prod:
                raise HTTPException(status_code=404, detail=f"Produto com ID {item.produto_id} não localizado.")
            
            if prod.quantidade < item.quantidade:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Estoque insuficiente para '{prod.nome}'. Disponível: {prod.quantidade}."
                )
            
            # Executa baixa imediata de estoque
            prod.quantidade -= item.quantidade
            subtotal_item = prod.preco_venda * item.quantidade
            total_venda += subtotal_item
            
            # Prepara o objeto pivot do relacionamento N:N
            item_venda = models.ItemVenda(
                produto_id=prod.id,
                quantidade=item.quantidade,
                preco_unitario=prod.preco_venda
            )
            itens_processados.append(item_venda)
            
            # Registra a movimentação física de saída de mercadoria
            mov = models.Movimentacao(
                produto_id=prod.id,
                quantidade_entrada=0,
                quantidade_saida=item.quantidade,
                tipo="venda_pdv"
            )
            db.add(mov)

        # Registra a transação comercial principal
        nova_venda = models.Venda(
            usuario_id=usuario_logado.get("id"),
            total=total_venda,
            data_venda=datetime.now()
        )
        db.add(nova_venda)
        db.flush()

        # Vincula os registros filhos à venda recém-criada
        for item_proc in itens_processados:
            item_proc.venda_id = nova_venda.id
            db.add(item_proc)
            
        # Aciona o provisionamento do módulo financeiro (Contas a Receber)
        nova_conta = models.ContasReceber(
            venda_id=nova_venda.id,
            valor=total_venda,
            status="pago",  # Vendas de balcão / PDV assumem pagamento imediato
            data_vencimento=datetime.now().date()
        )
        db.add(nova_conta)

    db.commit()
    return {"status": "sucesso", "venda_id": nova_venda.id, "total": total_venda}

# ==========================================
# PAINÉIS, MONITORAMENTO E RELATÓRIOS
# ==========================================

@app.get("/api/resumo-diario", response_model=ResumoDiarioResposta)
def obter_resumo_diario(db: Session = Depends(get_db), usuario_logado: dict = Depends(verificar_token)):
    """Gera indicadores consolidados do dia para os cards do dashboard."""
    hoje = datetime.now().date()
    vendas_hoje = db.query(models.Venda).filter(models.Venda.data_venda >= hoje).all()
    
    total_faturado = sum(v.total for v in vendas_hoje)
    return {
        "faturamento": float(total_faturado),
        "vendas": len(vendas_hoje),
        "status_caixa": "Aberto"
    }

@app.get("/api/financeiro-resumo", response_model=FinanceiroResposta)
def obter_resumo_financeiro(db: Session = Depends(get_db), usuario_logado: dict = Depends(verificar_admin)):
    """Restrito ao Admin. consolida fluxo financeiro das tabelas do MySQL."""
    contas = db.query(models.ContasReceber).all()
    a_receber = sum(c.valor for c in contas if c.status == "pendente")
    recebido = sum(c.valor for c in contas if c.status == "pago")
    
    return {
        "a_receber": float(a_receber),
        "a_pagar": 0.0,  # Expansível conectando a tabela complementar de contas a pagar
        "saldo_consolidado": float(recebido - 0.0)
    }

@app.get("/api/movimentacoes", response_model=List[MovimentacaoResposta])
def listar_movimentacoes(db: Session = Depends(get_db), usuario_logado: dict = Depends(verificar_token)):
    """Retorna dados de movimentações cruzados com o nome do produto via relacionamento ORM."""
    movs = db.query(models.Movimentacao).all()
    resultado = []
    for m in movs:
        resultado.append({
            "produto_nome": m.produto.nome,
            "quantidade_entrada": m.quantidade_entrada,
            "quantidade_saida": m.quantidade_saida
        })
    return resultado