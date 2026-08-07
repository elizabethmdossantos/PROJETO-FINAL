import os
import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

produtos_bp = Blueprint("produtos", __name__, url_prefix="/admin/produtos")

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _sessao_e_admin() -> bool:
    return session.get("perfil") == "admin"


def _headers() -> dict:
    return {"Authorization": f"Bearer {session.get('token')}"}


@produtos_bp.route("", methods=["GET"])
def listar():
    if not _sessao_e_admin():
        return redirect(url_for("auth.login"))

    produtos = []
    try:
        resposta = requests.get(
            f"{API_URL}/produtos",
            headers=_headers(),
            params={"apenas_ativos": "false"},
            timeout=5,
        )
        if resposta.status_code == 200:
            produtos = resposta.json()
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")

    return render_template(
        "admin/produtos.html", usuario=session.get("usuario"), produtos=produtos
    )


@produtos_bp.route("/novo", methods=["POST"])
def criar():
    if not _sessao_e_admin():
        return redirect(url_for("auth.login"))

    payload = {
        "codigo": request.form.get("codigo", "").strip(),
        "nome": request.form.get("nome", "").strip(),
        "preco": request.form.get("preco", "0"),
        "estoque": request.form.get("estoque", "0"),
        "disponivel_loja": request.form.get("disponivel_loja") == "on",
    }

    try:
        resposta = requests.post(
            f"{API_URL}/produtos", json=payload, headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")
        return redirect(url_for("produtos.listar"))

    if resposta.status_code != 201:
        mensagem = resposta.json().get("detail", "Não foi possível cadastrar o produto.")
        flash(mensagem, "erro")
    else:
        flash(f"Produto '{payload['nome']}' cadastrado com sucesso.", "sucesso")

    return redirect(url_for("produtos.listar"))


@produtos_bp.route("/<int:produto_id>/editar", methods=["POST"])
def editar(produto_id):
    if not _sessao_e_admin():
        return redirect(url_for("auth.login"))

    payload = {
        "nome": request.form.get("nome", "").strip(),
        "preco": request.form.get("preco", "0"),
        "estoque": request.form.get("estoque", "0"),
        "ativo": request.form.get("ativo") == "on",
        "disponivel_loja": request.form.get("disponivel_loja") == "on",
    }

    try:
        resposta = requests.patch(
            f"{API_URL}/produtos/{produto_id}", json=payload, headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")
        return redirect(url_for("produtos.listar"))

    if resposta.status_code != 200:
        mensagem = resposta.json().get("detail", "Não foi possível atualizar o produto.")
        flash(mensagem, "erro")
    else:
        flash("Produto atualizado com sucesso.", "sucesso")

    return redirect(url_for("produtos.listar"))
