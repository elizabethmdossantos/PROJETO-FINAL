import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

pdv_bp = Blueprint("pdv", __name__, url_prefix="/pdv")

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _logado() -> bool:
    return bool(session.get("token"))


def _headers() -> dict:
    return {"Authorization": f"Bearer {session.get('token')}"}


def _caixa_atual():
    try:
        resposta = requests.get(f"{API_URL}/caixa/atual", headers=_headers(), timeout=5)
    except requests.exceptions.RequestException:
        return None
    if resposta.status_code == 200:
        return resposta.json()
    return None


@pdv_bp.route("/caixa", methods=["GET"])
def caixa():
    if not _logado():
        return redirect(url_for("auth.login"))

    caixa_aberto = _caixa_atual()
    return render_template(
        "pdv/caixa.html",
        usuario=session.get("usuario"),
        caixa_aberto=caixa_aberto,
        resumo=None,
    )


@pdv_bp.route("/caixa/abrir", methods=["POST"])
def abrir_caixa():
    if not _logado():
        return redirect(url_for("auth.login"))

    payload = {
        "valor_abertura": request.form.get("valor_abertura", "0"),
        "observacoes": request.form.get("observacoes") or None,
    }
    try:
        resposta = requests.post(
            f"{API_URL}/caixa/abrir", json=payload, headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")
        return redirect(url_for("pdv.caixa"))

    if resposta.status_code != 201:
        mensagem = resposta.json().get("detail", "Não foi possível abrir o caixa.")
        flash(mensagem, "erro")
        return redirect(url_for("pdv.caixa"))

    return redirect(url_for("pdv.terminal"))


@pdv_bp.route("/caixa/fechar", methods=["POST"])
def fechar_caixa():
    if not _logado():
        return redirect(url_for("auth.login"))

    payload = {
        "valor_fechamento": request.form.get("valor_fechamento", "0"),
        "observacoes": request.form.get("observacoes") or None,
    }
    try:
        resposta = requests.post(
            f"{API_URL}/caixa/fechar", json=payload, headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")
        return redirect(url_for("pdv.caixa"))

    if resposta.status_code != 200:
        mensagem = resposta.json().get("detail", "Não foi possível fechar o caixa.")
        flash(mensagem, "erro")
        return redirect(url_for("pdv.caixa"))

    resumo = resposta.json()
    return render_template(
        "pdv/caixa.html",
        usuario=session.get("usuario"),
        caixa_aberto=None,
        resumo=resumo,
    )


@pdv_bp.route("/terminal", methods=["GET"])
def terminal():
    if not _logado():
        return redirect(url_for("auth.login"))

    caixa_aberto = _caixa_atual()
    if not caixa_aberto:
        flash("Abra o caixa antes de iniciar as vendas.", "erro")
        return redirect(url_for("pdv.caixa"))

    return render_template(
        "pdv/terminal.html", usuario=session.get("usuario"), caixa_aberto=caixa_aberto
    )


@pdv_bp.route("/terminal/buscar-produto", methods=["POST"])
def buscar_produto():
    if not _logado():
        return jsonify({"detail": "Sessão expirada."}), 401

    codigo = (request.get_json(silent=True) or {}).get("codigo", "").strip()
    if not codigo:
        return jsonify({"detail": "Informe um código de produto."}), 400

    try:
        resposta = requests.get(
            f"{API_URL}/produtos/codigo/{codigo}", headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        return jsonify({"detail": "Não foi possível conectar à API."}), 502

    return jsonify(resposta.json()), resposta.status_code


@pdv_bp.route("/pedidos-online", methods=["GET"])
def pedidos_online():
    if not _logado():
        return redirect(url_for("auth.login"))

    caixa_aberto = _caixa_atual()
    pedidos = []
    try:
        resposta = requests.get(
            f"{API_URL}/pedidos-online",
            headers=_headers(),
            params={"status_filtro": "aguardando_retirada"},
            timeout=5,
        )
        if resposta.status_code == 200:
            pedidos = resposta.json()
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")

    return render_template(
        "pdv/pedidos_online.html",
        usuario=session.get("usuario"),
        caixa_aberto=caixa_aberto,
        pedidos=pedidos,
    )


@pdv_bp.route("/pedidos-online/<int:pedido_id>/retirar", methods=["POST"])
def retirar_pedido_online(pedido_id):
    if not _logado():
        return redirect(url_for("auth.login"))

    try:
        resposta = requests.post(
            f"{API_URL}/pedidos-online/{pedido_id}/retirar", headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")
        return redirect(url_for("pdv.pedidos_online"))

    if resposta.status_code != 200:
        mensagem = resposta.json().get("detail", "Não foi possível confirmar a retirada.")
        flash(mensagem, "erro")
    else:
        pedido = resposta.json()
        flash(
            f"Pedido {pedido['numero_pedido']} entregue e lançado no caixa como venda.",
            "sucesso",
        )

    return redirect(url_for("pdv.pedidos_online"))


@pdv_bp.route("/terminal/finalizar", methods=["POST"])
def finalizar_venda():
    if not _logado():
        return jsonify({"detail": "Sessão expirada."}), 401

    dados = request.get_json(silent=True) or {}
    payload = {
        "forma_pagamento": dados.get("forma_pagamento"),
        "itens": dados.get("itens", []),
    }
    try:
        resposta = requests.post(
            f"{API_URL}/vendas", json=payload, headers=_headers(), timeout=5
        )
    except requests.exceptions.RequestException:
        return jsonify({"detail": "Não foi possível conectar à API."}), 502

    return jsonify(resposta.json()), resposta.status_code
