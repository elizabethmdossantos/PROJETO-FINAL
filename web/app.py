from flask import Flask, render_template, request, redirect, url_for, flash
import requests

app = Flask(__name__)
app.secret_key = "chave_secreta_para_alertas" # Necessário para usar o 'flash' message do Flask

# URL base da nossa API FastAPI que você acabou de ligar
API_URL = "http://127.0.0.1:8000/api"

# 1. Rota da Dashboard (Página Principal)
@app.route('/')
@app.route('/dashboard')
def dashboard():
    # Por enquanto renderiza a tela estática, depois buscaremos os dados do caixa na API
    return render_template('dashboard_admin.html')

# 2. Rota do Formulário de Cadastro de Produtos
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_produto():
    if request.method == 'POST':
        # Captura os dados vindos do formulário HTML
        dados_produto = {
            "nome": request.form.get('nome-produto'),
            "codigo": request.form.get('codigo-produto'),
            "preco_custo": float(request.form.get('preco-custo')),
            "preco_venda": float(request.form.get('preco-venda')),
            "categoria": request.form.get('categoria'),
            "quantidade": int(request.form.get('quantidade'))
        }

        try:
            # Envia os dados via POST HTTP para a API do FastAPI salvar no MySQL
            resposta = requests.post(f"{API_URL}/produtos", json=dados_produto)
            
            if resposta.status_code == 201:
                flash("Produto cadastrado com sucesso!", "success")
            else:
                erro_msg = resposta.json().get('detail', 'Erro ao cadastrar.')
                flash(f"Erro na API: {erro_msg}", "danger")
                
        except requests.exceptions.ConnectionError:
            flash("Erro crítico: Não foi possível conectar à API Backend.", "danger")

        return redirect(url_for('cadastro_produto'))

    return render_template('cadastro_produto.html')

# 3. Rota de Estoque
@app.route('/estoque')
def estoque():
    return render_template('estoque.html')

# 4. Rota do Financeiro
@app.route('/financeiro')
def financeiro():
    return render_template('financeiro.html')

# 5. Rota de Relatórios
@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)