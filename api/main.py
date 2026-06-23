from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import obter_conexao
from app.models.cadastro_produto import ProdutoCadastro

app = FastAPI(
    title="API de Gestão Comercial",
    description="Núcleo do sistema - Controle de Estoque e Finanças",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/produtos", status_code=status.HTTP_201_CREATED)
def cadastrar_produto(produto: ProdutoCadastro):
    conexao = obter_conexao()
    if not conexao:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao banco de dados.")
    
    cursor = conexao.cursor()
    try:
        # 1. Inserir o produto na tabela 'produtos'
        sql_produto = """
            INSERT INTO produtos (nome, codigo, preco_custo, preco_venda, categoria, quantidade)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores_produto = (
            produto.nome, produto.codigo, produto.preco_custo, 
            produto.preco_venda, produto.categoria, produto.quantidade
        )
        cursor.execute(sql_produto, valores_produto)
        produto_id = cursor.lastrowid # Pega o ID gerado pelo banco

        # 2. Registrar a entrada inicial na tabela 'movimentacoes_estoque'
        sql_movimentacao = """
            INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade)
            VALUES (%s, %s, %s)
        """
        valores_movimentacao = (produto_id, 'compra', produto.quantidade)
        cursor.execute(sql_movimentacao, valores_movimentacao)

        # Confirma as alterações no banco
        conexao.commit()
        return {"mensagem": "Produto e movimentação cadastrados com sucesso!", "id": produto_id}

    except Exception as e:
        conexao.rollback() # Cancela tudo se der erro no meio do caminho
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="Já existe um produto cadastrado com este código.")
        raise HTTPException(status_code=500, detail=f"Erro interno ao salvar: {str(e)}")
    
    finally:
        cursor.close()
        conexao.close()