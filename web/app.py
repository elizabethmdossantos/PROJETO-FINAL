"""
Cria as rotas que o usuário digita no navedagor.
Captura o que o usuário digitou nos formulários html.
Faz ligação(requests) para o main(FastAPI), envia o token de segurança e joga os dados para lá.
Quando a API responde, ele pega os dados JSON, injeta dentro dos html e entrega a página pronta.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
import requests
# inicia o Flask
app = Flask(__name__)
# chave secreta
app.secret_key = "chave_seguranca_sistema"
# endereço API
API_URL = "http://127.0.0.1:8000"

# FUNÇÕES AUXILIARES
def obter_headers_autenticados():
    token = session.get('token')
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

@app.before_request
def verificar_sessao_usuario():
    rotas_publicas = ['login', 'static']
    if request.endpoint not in rotas_publicas and 'token' not in session:
        return redirect(url_for('login'))

# ROTA DE LOGIN DO FLASK
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        
        try:
            resposta = requests.post(f"{API_URL}/api/auth/login", json={"usuario": usuario, "senha": senha}, timeout=5)
            if resposta.status_code == 200:
                # Salva o token JWT na sessão do Flask
                session['token'] = resposta.json().get('access_token')
                session['usuario'] = usuario
                flash("Bem-vindo ao sistema!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Usuário ou senha inválidos.", "danger")
        except requests.RequestException:
            flash("Erro de conexão com o servidor de autenticação.", "danger")
            
    return render_template('login.html') # Crie um arquivo login.html simples na sua pasta templates

@app.route('/logout')
def logout():
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for('login'))

# ROTAS DE INTERFACE DO USUÁRIO

@app.route('/')
@app.route('/dashboard')
def dashboard():
    resumo = {"faturamento": 0.0, "vendas": 0, "status_caixa": "Indisponível"}
    try:
        resposta = requests.get(f"{API_URL}/api/resumo-diario", headers=obter_headers_autenticados(), timeout=5)
        if resposta.status_code == 200:
            resumo = resposta.json()
    except requests.RequestException:
        flash("Erro crítico: Sem comunicação com o servidor backend.", "danger")
    
    return render_template('dashboard_admin.html', resumo=resumo)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_produto():
    if request.method == 'POST':
        dados_formulario = {
            "nome": request.form.get('nome-produto', '').strip(),
            "codigo": request.form.get('codigo-produto', '').strip(),
            "preco_custo": float(request.form.get('preco-custo', 0)),
            "preco_venda": float(request.form.get('preco-venda', 0)),
            "categoria": request.form.get('categoria', '').strip(),
            "quantidade": int(request.form.get('quantidade', 0))
        }
        try:
            resposta = requests.post(f"{API_URL}/api/produtos", json=dados_formulario, headers=obter_headers_autenticados(), timeout=5)
            if resposta.status_code == 201:
                flash("Produto cadastrado com sucesso!", "success")
                return redirect(url_for('cadastro_produto'))
            else:
                erro_detalhe = resposta.json().get('detail', 'Erro no processamento.')
                flash(f"Falha na validação: {erro_detalhe}", "danger")
        except requests.RequestException:
            flash("Erro crítico: Conexão com a API indisponível.", "danger")
            
    return render_template('cadastro_produto.html')

@app.route('/estoque')
def estoque():
    produtos = []
    movimentacoes = []
    headers = obter_headers_autenticados()
    try:
        resp_prod = requests.get(f"{API_URL}/api/produtos", headers=headers, timeout=5)
        resp_mov = requests.get(f"{API_URL}/api/movimentacoes", headers=headers, timeout=5)
        if resp_prod.status_code == 200:
            produtos = resp_prod.json()
        if resp_mov.status_code == 200:
            movimentacoes = resp_mov.json()
    except requests.RequestException:
        flash("Erro ao conectar à API para obter dados de estoque.", "danger")
        
    return render_template('estoque.html', produtos=produtos, movimentacoes=movimentacoes)

@app.route('/financeiro')
def financeiro():
    dados_fin = {"a_receber": 0.0, "a_pagar": 0.0, "saldo_consolidated": 0.0} # Ajustado chave do mock anterior
    try:
        resposta = requests.get(f"{API_URL}/api/financeiro-resumo", headers=obter_headers_autenticados(), timeout=5)
        if resposta.status_code == 200:
            dados_fin = resposta.json()
    except requests.RequestException:
        flash("Aviso: Dados financeiros indisponíveis no momento.", "warning")
        
    return render_template('financeiro.html', financeiro=dados_fin)

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')


"""
@app.route('/pdv')
def pdv():
    return render_template('pdv.html')
"""

if __name__ == '__main__':
    app.run(debug=True, port=5001)