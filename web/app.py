from flask import Flask, render_template, request, redirect, url_for, flash, Response
import requests

app = Flask(__name__)
app.secret_key = "chave_secreta"

# URL base da API FastAPI
API_URL = "http://127.0.0.1:8000"

# ==============================================================================
# 1. ROTA DA DASHBOARD
# ==============================================================================
@app.route('/')
@app.route('/dashboard')
def dashboard():
    dados_resumo = {
        "faturamento": 0.0,
        "vendas": 0,
        "status_caixa": "Indisponível"
    }
    try:
        resposta = requests.get(f"{API_URL}/resumo-diario", timeout=5)
        if resposta.status_code == 200:
            dados_resumo = resposta.json()
        else:
            flash("Aviso: Não foi possível atualizar os indicadores do dashboard.", "warning")
    except Exception:
        flash("Erro: Não foi possível conectar à API para carregar o resumo.", "danger")

    return render_template('dashboard_admin.html', resumo=dados_resumo)


# ==============================================================================
# 2. ROTA DE CADASTRO DE PRODUTOS
# ==============================================================================
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_produto():
    if request.method == 'POST':
        nome = request.form.get('nome-produto')
        codigo = request.form.get('codigo-produto')
        preco_custo_raw = request.form.get('preco-custo')
        preco_venda_raw = request.form.get('preco-venda')
        categoria = request.form.get('categoria')
        quantidade_raw = request.form.get('quantidade')

        if not all([nome, codigo, preco_custo_raw, preco_venda_raw, quantidade_raw]):
            flash("Todos os campos são obrigatórios!", "danger")
            return redirect(url_for('cadastro_produto'))

        try:
            dados_produto = {
                "nome": nome.strip(),
                "codigo": str(codigo).strip(),
                "preco_custo": float(preco_custo_raw),
                "preco_venda": float(preco_venda_raw),
                "categoria": categoria.strip(),
                "quantidade": int(quantidade_raw)
            }
            
            resposta = requests.post(f"{API_URL}/api/produtos", json=dados_produto, timeout=5)
            
            if resposta.status_code == 201:
                flash("Produto cadastrado com sucesso!", "success")
            else:
                erro_json = resposta.json()
                detalhe = erro_json.get('detail')
                if isinstance(detalhe, list):
                    mensagens_erro = [f"{err.get('loc', [])[-1]}: {err.get('msg')}" for err in detalhe]
                    erro_msg = " | ".join(mensagens_erro)
                else:
                    erro_msg = detalhe or 'Erro inesperado no servidor.'
                flash(f"Erro na API: {erro_msg}", "danger")
                
        except ValueError:
            flash("Erro de formato: Preços e quantidade devem ser numéricos.", "danger")
        except Exception:
            flash("Erro crítico: Não foi possível conectar à API Backend.", "danger")

        return redirect(url_for('cadastro_produto'))

    return render_template('cadastro_produto.html')


# ==============================================================================
# 3. ROTA DE ESTOQUE
# ==============================================================================
@app.route('/estoque')
def estoque():
    produtos = []
    movimentacoes = []
    try:
        resposta_produtos = requests.get(f"{API_URL}/produtos", timeout=5)
        if resposta_produtos.status_code == 200:
            produtos = resposta_produtos.json()

        resposta_movimentacoes = requests.get(f"{API_URL}/movimentacoes", timeout=5)
        if resposta_movimentacoes.status_code == 200:
            movimentacoes = resposta_movimentacoes.json()
    except Exception:
        flash("Erro: Não foi possível conectar à API para carregar o estoque.", "danger")

    return render_template('estoque.html', produtos=produtos, movimentacoes=movimentacoes)


# ==============================================================================
# 4. ROTA DO FINANCEIRO
# ==============================================================================
@app.route('/financeiro')
def financeiro():
    dados_financeiros = {"a_receber": 0.0, "a_pagar": 0.0, "saldo_consolidado": 0.0}
    try:
        resposta = requests.get(f"{API_URL}/financeiro-resumo", timeout=5)
        if resposta.status_code == 200:
            dados_financeiros = resposta.json()
    except Exception:
        flash("Aviso: Não foi possível buscar dados financeiros em tempo real.", "warning")
        
    return render_template('financeiro.html', financeiro=dados_financeiros)


# ==============================================================================
# 5. ROTAS DE RELATÓRIOS
# ==============================================================================
@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')


@app.route('/relatorios/faturamento', methods=['POST'])
def gerar_relatorio_faturamento():
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')
    try:
        resposta = requests.get(
            f"{API_URL}/relatorios/exportar", 
            params={"tipo_relatorio": "faturamento", "formato": "pdf", "data_inicio": data_inicio, "data_fim": data_fim},
            timeout=10
        )
        if resposta.status_code == 200:
            return Response(
                resposta.content,
                mimetype="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=relatorio_faturamento_{data_inicio}_a_{data_fim}.pdf"}
            )
        else:
            flash("Aviso: O módulo de arquivos PDF está em desenvolvimento na API.", "warning")
    except Exception:
        flash("Erro: Falha ao conectar à API para gerar o relatório.", "danger")
        
    return redirect(url_for('relatorios'))


@app.route('/relatorios/vendas', methods=['POST'])
def gerar_relatorio_vendas():
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')
    try:
        resposta = requests.get(
            f"{API_URL}/relatorios/exportar", 
            params={"tipo_relatorio": "itens_vendidos", "formato": "xlsx", "data_inicio": data_inicio, "data_fim": data_fim},
            timeout=10
        )
        if resposta.status_code == 200:
            return Response(
                resposta.content,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=relatorio_vendas_{data_inicio}_a_{data_fim}.xlsx"}
            )
        else:
            flash("Aviso: O módulo de arquivos Excel está em desenvolvimento na API.", "warning")
    except Exception:
        flash("Erro: Falha ao conectar à API para gerar o relatório.", "danger")
        
    return redirect(url_for('relatorios'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)