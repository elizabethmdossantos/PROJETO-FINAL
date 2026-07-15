import os
import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _sessao_e_admin() -> bool:
    return session.get("perfil") == "admin"


def _headers() -> dict:
    return {"Authorization": f"Bearer {session.get('token')}"}


@admin_bp.route("/dashboard")
def dashboard():
    if not _sessao_e_admin():
        return redirect(url_for("auth.login"))

    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    vendas, produtos, caixas = [], [], []
    try:
        params = {}
        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim

        resp_vendas = requests.get(
            f"{API_URL}/vendas", headers=_headers(), params=params, timeout=5
        )
        if resp_vendas.status_code == 200:
            vendas = resp_vendas.json()

        resp_produtos = requests.get(f"{API_URL}/produtos", headers=_headers(), timeout=5)
        if resp_produtos.status_code == 200:
            produtos = resp_produtos.json()

        resp_caixas = requests.get(f"{API_URL}/caixa", headers=_headers(), timeout=5)
        if resp_caixas.status_code == 200:
            caixas = resp_caixas.json()
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")

    vendas_concluidas = [v for v in vendas if v.get("status") == "concluida"]
    total_vendido = sum(float(v["valor_total"]) for v in vendas_concluidas)
    quantidade_vendas = len(vendas_concluidas)
    produtos_estoque_baixo = [p for p in produtos if p["estoque"] <= 5]

    return render_template(
        "admin/dashboard.html",
        usuario=session.get("usuario"),
        vendas=vendas,
        produtos=produtos,
        caixas=caixas,
        total_vendido=total_vendido,
        quantidade_vendas=quantidade_vendas,
        produtos_estoque_baixo=produtos_estoque_baixo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@admin_bp.route("/vendas/<int:venda_id>/cancelar", methods=["POST"])
def cancelar_venda(venda_id):
    if not _sessao_e_admin():
        return redirect(url_for("auth.login"))

    try:
        resposta = requests.post(
            f"{API_URL}/vendas/{venda_id}/cancelar", headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")
        return redirect(url_for("admin.dashboard"))

    if resposta.status_code != 200:
        mensagem = resposta.json().get("detail", "Não foi possível cancelar a venda.")
        flash(mensagem, "erro")
    else:
        flash(f"Venda #{venda_id} cancelada e estoque devolvido.", "sucesso")

    data_inicio = request.form.get("data_inicio", "")
    data_fim = request.form.get("data_fim", "")
    return redirect(url_for("admin.dashboard", data_inicio=data_inicio, data_fim=data_fim))
