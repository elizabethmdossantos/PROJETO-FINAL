import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint("auth", __name__)

API_URL = os.getenv("API_URL", "http://localhost:8000")


@auth_bp.route("/")
def raiz():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", e_admin=False)

    login_usuario = request.form.get("login", "").strip()
    senha = request.form.get("senha", "")
    e_admin = request.form.get("e_admin") == "on"
    senha_admin = request.form.get("senha_admin", "")

    payload = {
        "login": login_usuario,
        "senha": senha,
        "perfil_solicitado": "admin" if e_admin else "caixa",
    }
    if e_admin:
        payload["senha_admin"] = senha_admin

    try:
        resposta = requests.post(f"{API_URL}/auth/login", json=payload, timeout=5)
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à API. Verifique se ela está no ar.", "erro")
        return render_template("login.html", e_admin=e_admin), 502

    if resposta.status_code != 200:
        try:
            mensagem = resposta.json().get("detail", "Login ou senha incorretos.")
        except ValueError:
            mensagem = "Login ou senha incorretos."
        flash(mensagem, "erro")
        return render_template("login.html", e_admin=e_admin), resposta.status_code

    dados = resposta.json()
    session["token"] = dados["access_token"]
    session["usuario"] = dados["usuario"]["nome"]
    session["perfil"] = dados["usuario"]["perfil"]

    if session["perfil"] == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("pdv.caixa"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
