"""
Aplicação Web (Flask): Camada de Experiência e Visão do Usuário.
Consome exclusivamente a API via requisições JSON e renderiza páginas em Jinja2.
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests

app = Flask(__name__)
# Configuração segura via variáveis de ambiente
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave_fallback_sessao_flask_2026")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def obter_headers_autenticados():
    """Recupera dinamicamente o Token de dentro do cookie de sessão cifrado do Flask."""
    token = session.get('token')
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

@app.before_request
def verificar_sessao_usuario():
    """Garante controle estrito de rotas públicas e privadas no ecossistema Web."""
    rotas_publicas = ['login', 'static']
    if request.endpoint not in rotas_publicas and 'token' not in session:
        return redirect(url_for('login'))

# ==========================================
# GESTÃO DE SESSÃO E ACESSO
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        
        try:
            resposta = requests.post(
                f"{API_URL}/api/auth/login", 
                json={"usuario": usuario, "senha": senha}, 
                timeout=5
            )
            if resposta.status_code == 200:
                corpo_resposta = resposta.json()
                # Persiste as informações do JWT na sessão segura do cookie
                session['token'] = corpo_resposta.get('access_token')
                session['usuario'] = usuario
                session['perfil'] = corpo_resposta.get('perfil')
                
                flash("Login efetuado com sucesso!", "success")
                return redirect(url_for('dashboard'))
            else:
                erro_msg = resposta.json().get('detail', 'Credenciais inválidas.')
                flash(f"Erro na autenticação: {erro_msg}", "danger")
        except requests.RequestException:
            flash("Conexão interrompida com a API central do ERP.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sessão finalizada.", "info")
    return redirect(url_for('login'))

# ==========================================
# ROTAS DE INTERFACE DE USUÁRIO (VIEW)
# ==========================================

@app.route('/')
@app.route('/dashboard')
def dashboard():
    resumo = {"faturamento": 0.0, "vendas": 0, "status_caixa": "Desconectado"}
    try:
        resposta = requests.get(f"{API_URL}/api/resumo-diario", headers=obter_headers_autenticados(), timeout=5)
        if resposta.status_code == 200:
            resumo = resposta.json()
    except requests.RequestException:
        flash("Instabilidade detectada na leitura dos dados da API.", "danger")
    
    return render_template('dashboard_admin.html', resumo=resumo)

@app.route('/registrar', methods=['POST'])
def registrar_usuario_ponte():
    dados_tela = request.get_json()
    
    # Monta os dados exatamente como sua API com o schema UsuarioCadastro espera
    payload = {
        "username": dados_tela.get("username"),
        "senha": dados_tela.get("password"), 
        "perfil": dados_tela.get("perfil", "vendedor")
    }
    
    try:
        # Repassa para a sua API central de auth
        resposta_api = requests.post(f"{API_URL}/api/auth/registrar", json=payload)
        
        if resposta_api.status_code == 201:
            return jsonify({"status": "sucesso", "message": "Usuário criado com sucesso!"}), 200
        else:
            erro_msg = resposta_api.json().get("detail", "Erro ao realizar cadastro.")
            return jsonify({"status": "erro", "message": erro_msg}), resposta_api.status_code
            
    except requests.RequestException:
        return jsonify({"status": "erro", "message": "Conexão interrompida com a API central"}), 500

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_produto():
    # RBAC a nível de Front-end: Impede que vendedores acessem a view de cadastro
    if session.get('perfil') != 'administrador':
        flash("Acesso restrito. Sua conta não possui permissões administrativas.", "warning")
        return redirect(url_for('dashboard'))

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
            resposta = requests.post(
                f"{API_URL}/api/produtos", 
                json=dados_formulario, 
                headers=obter_headers_autenticados(), 
                timeout=5
            )
            if resposta.status_code == 201:
                flash("Produto integrado com sucesso ao catálogo!", "success")
                return redirect(url_for('estoque'))
            else:
                detalhe = resposta.json().get('detail', 'Ocorreu um erro inesperado.')
                flash(f"Erro na validação da API: {detalhe}", "danger")
        except requests.RequestException:
            flash("Falha ao submeter dados. Verifique a API.", "danger")
            
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
        flash("Ocorreu um erro ao carregar os dados de inventário.", "danger")
        
    return render_template('estoque.html', produtos=produtos, movimentacoes=movimentacoes)

@app.route('/financeiro')
def financeiro():
    if session.get('perfil') != 'administrador':
        flash("Módulo financeiro restrito à gestão corporativa.", "warning")
        return redirect(url_for('dashboard'))

    dados_fin = {"a_receber": 0.0, "a_pagar": 0.0, "saldo_consolidado": 0.0}
    try:
        resposta = requests.get(f"{API_URL}/api/financeiro-resumo", headers=obter_headers_autenticados(), timeout=5)
        if resposta.status_code == 200:
            dados_fin = resposta.json()
    except requests.RequestException:
        flash("Não foi possível consolidar o balanço financeiro.", "warning")
        
    return render_template('financeiro.html', financeiro=dados_fin)

# ==========================================
# FLUXO DO PONTO DE VENDA (PDV)
# ==========================================

@app.route('/pdv')
def pdv():
    """Renderiza a interface do operador de caixa e injeta os produtos disponíveis."""
    produtos = []
    try:
        resposta = requests.get(f"{API_URL}/api/produtos", headers=obter_headers_autenticados(), timeout=5)
        if resposta.status_code == 200:
            produtos = resposta.json()
    except requests.RequestException:
        flash("Impossível carregar catálogo para vendas imediatas.", "danger")
    return render_template('pdv.html', produtos=produtos)

@app.route('/pdv/confirmar-venda', methods=['POST'])
def confirmar_venda():
    """Recebe o payload estruturado em JSON gerado pelo seu arquivo JS do PDV."""
    dados_carrinho = request.get_json()
    try:
        resposta = requests.post(
            f"{API_URL}/api/vendas",
            json=dados_carrinho,
            headers=obter_headers_autenticados(),
            timeout=5
        )
        if resposta.status_code == 201:
            return jsonify({"status": "sucesso", "mensagem": "Transação comercial homologada!"}), 201
        else:
            erro_msg = resposta.json().get('detail', 'Erro indeterminado no checkout.')
            return jsonify({"status": "erro", "mensagem": erro_msg}), resposta.status_code
    except requests.RequestException:
        return jsonify({"status": "erro", "mensagem": "Conexão de rede indisponível com o servidor central."}), 503

if __name__ == '__main__':
    app.run(debug=True, port=5001)