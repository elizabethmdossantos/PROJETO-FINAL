import sys
import os
# Adiciona a pasta atual ('api') ao caminho de busca do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Seus imports originais continuam aqui embaixo...
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import obter_conexao
from app.models.cadastro_produto import ProdutoCadastro
from fastapi.responses import FileResponse

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

# 1. CADASTRAR PRODUTO
@app.post("/api/produtos", status_code=status.HTTP_201_CREATED)
def cadastrar_produto(produto: ProdutoCadastro):
    conexao = obter_conexao()
    if not conexao:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao banco de dados.")
    
    cursor = conexao.cursor()
    try:
        sql_produto = """
            INSERT INTO produtos (nome, codigo, preco_custo, preco_venda, categoria, quantidade)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores_produto = (
            produto.nome, produto.codigo, produto.preco_custo, 
            produto.preco_venda, produto.categoria, produto.quantidade
        )
        cursor.execute(sql_produto, valores_produto)
        produto_id = cursor.lastrowid 

        sql_movimentacao = """
            INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade)
            VALUES (%s, %s, %s)
        """
        valores_movimentacao = (produto_id, 'compra', produto.quantidade)
        cursor.execute(sql_movimentacao, valores_movimentacao)

        conexao.commit()
        return {"mensagem": "Produto e movimentação cadastrados com sucesso!", "id": produto_id}

    except Exception as e:
        conexao.rollback() 
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="Já existe um produto cadastrado com este código.")
        raise HTTPException(status_code=500, detail=f"Erro interno ao salvar: {str(e)}")
    
    finally:
        cursor.close()
        conexao.close()


# 2. LISTAR PRODUTOS (Tela de Estoque)
@app.get("/api/produtos")
def listar_produtos():
    conexao = obter_conexao()
    if not conexao:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco.")
    
    # dictionary=True faz o banco retornar como dicionário/JSON
    cursor = conexao.cursor(dictionary=True) 
    try:
        cursor.execute("SELECT nome, quantidade FROM produtos ORDER BY nome ASCE")
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexao.close()


# 3. LISTAR MOVIMENTAÇÕES (Tela de Estoque)
@app.get("/api/movimentacoes")
def listar_movimentacoes():
    conexao = obter_conexao()
    if not conexao:
        raise HTTPException(status_code=500, detail="Erro de conexão.")
        
    cursor = conexao.cursor(dictionary=True)
    try:
        # Faz um JOIN para buscar o nome do produto e agrupa/separa entradas e saídas
        sql = """
            SELECT 
                p.nome AS produto_nome,
                SUM(CASE WHEN m.tipo = 'compra' THEN m.quantidade ELSE 0 END) AS quantidade_entrada,
                SUM(CASE WHEN m.tipo = 'venda' THEN m.quantidade ELSE 0 END) AS quantidade_saida
            FROM movimentacoes_estoque m
            JOIN produtos p ON m.produto_id = p.id
            GROUP BY p.id, p.nome
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexao.close()


# 4. RESUMO DIÁRIO (Dashboard)
@app.get("/api/resumo-diario")
def obter_resumo_diario():
    conexao = obter_conexao()
    if not conexao:
        raise HTTPException(status_code=500, detail="Erro de conexão.")
        
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(p.preco_venda * m.quantidade), 0.0) AS faturamento,
                COUNT(DISTINCT m.id) AS vendas
            FROM movimentacoes_estoque m
            JOIN produtos p ON m.produto_id = p.id
            WHERE m.tipo = 'venda' AND DATE(m.data_criacao) = CURDATE()
        """)
        resultado = cursor.fetchone()
        
        return {
            "faturamento": float(resultado["faturamento"]),
            "vendas": int(resultado["vendas"]),
            "status_caixa": "Aberto"
        }
    except Exception as e:
        # Se as tabelas de vendas não existirem ainda, devolve dados mocados para não quebrar a tela
        return {"faturamento": 0.0, "vendas": 0, "status_caixa": "Aberto"}
    finally:
        cursor.close()
        conexao.close()

# 5. RESUMO FINANCEIRO (Para alimentar a Tela de Financeiro)
@app.get("/api/financeiro-resumo")
def obter_resumo_financeiro():
    conexao = obter_conexao()
    if not conexao:
        raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")
        
    cursor = conexao.cursor(dictionary=True)
    try:
        # Exemplo de lógica para calcular os valores com base no seu banco
        # Você pode adaptar as tabelas abaixo ('contas_receber', 'contas_pagar') conforme sua estrutura real
        
        # Simulando cálculo de contas a receber (ex: vendas a prazo ou pendentes)
        cursor.execute("SELECT COALESCE(SUM(valor), 0.0) AS total FROM contas_receber WHERE status = 'pendente'")
        a_receber = cursor.fetchone()["total"]
        
        # Simulando cálculo de contas a pagar (ex: despesas pendentes)
        cursor.execute("SELECT COALESCE(SUM(valor), 0.0) AS total FROM contas_pagar WHERE status = 'pendente'")
        a_pagar = cursor.fetchone()["total"]
        
        # Saldo consolidado simplificado (Entradas - Saídas)
        saldo_consolidado = float(a_receber) - float(a_pagar)
        
        return {
            "a_receber": float(a_receber),
            "a_pagar": float(a_pagar),
            "saldo_consolidado": saldo_consolidado
        }
    except Exception as e:
        # Caso você ainda não tenha as tabelas financeiras criadas no banco,
        # retornamos valores zerados para permitir que o frontend abra sem quebrar
        return {
            "a_receber": 0.0,
            "a_pagar": 0.0,
            "saldo_consolidado": 0.0
        }
    finally:
        cursor.close()
        conexao.close()


# 7. GERAR ARQUIVO DE RELATÓRIO (Exemplo de exportação)
@app.get("/api/relatorios/exportar")
def exportar_relatorio(tipo_relatorio: str, formato: str):
    # tipo_relatorio: 'faturamento' ou 'itens_vendidos'
    # formato: 'pdf' ou 'xlsx'
    
    try:
        # Aqui dentro viria a sua lógica usando bibliotecas como 'pandas' (para Excel) 
        # ou 'reportlab'/'pdfkit' (para PDF) para criar o arquivo dinamicamente.
        
        # Caminho onde o arquivo gerado seria salvo temporariamente no servidor
        caminho_arquivo = f"relatorios_temporarios/relatorio_{tipo_relatorio}.{formato}"
        
        # (Código fictício de geração do arquivo...)
        # Se o arquivo existir, envia para o navegador do cliente iniciar o download:
        if os.path.exists(caminho_arquivo):
            media_type = "application/pdf" if formato == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return FileResponse(
                path=caminho_arquivo, 
                filename=f"relatorio_{tipo_relatorio}_{date.today()}.{formato}",
                media_type=media_type
            )
        
        # Enquanto você não implementa a geração real do PDF/Excel, devolvemos um erro controlado:
        raise HTTPException(status_code=511, detail="Módulo de geração de arquivos em desenvolvimento.")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar arquivo: {str(e)}")