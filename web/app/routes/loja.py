import os
import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

loja_bp = Blueprint("loja", __name__, url_prefix="/loja")

API_URL = os.getenv("API_URL", "http://localhost:8000")

CHAVE_CARRINHO = "carrinho_feira"


def _carrinho() -> dict:
    """Carrinho fica na sessão do Flask (não em cookie/localStorage do
    navegador): {produto_id (str): quantidade (int)}."""
    return session.setdefault(CHAVE_CARRINHO, {})


def _salvar_carrinho(carrinho: dict) -> None:
    session[CHAVE_CARRINHO] = carrinho
    session.modified = True


def _buscar_catalogo(busca: str = "") -> list:
    try:
        resposta = requests.get(
            f"{API_URL}/catalogo", params={"busca": busca}, timeout=5
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à loja agora. Tente novamente em instantes.", "erro")
        return []
    if resposta.status_code != 200:
        return []
    return resposta.json()


def _itens_do_carrinho() -> list:
    """Recarrega os itens do carrinho a partir do catálogo atual, para sempre
    mostrar preço e disponibilidade em dia (produto pode ter mudado desde que
    foi adicionado)."""
    carrinho = _carrinho()
    if not carrinho:
        return []
    catalogo = {str(p["id"]): p for p in _buscar_catalogo()}
    itens = []
    for produto_id, quantidade in carrinho.items():
        produto = catalogo.get(produto_id)
        if not produto:
            continue
        subtotal = round(float(produto["preco"]) * quantidade, 2)
        itens.append(
            {
                "produto_id": produto_id,
                "codigo": produto["codigo"],
                "nome": produto["nome"],
                "preco": float(produto["preco"]),
                "quantidade": quantidade,
                "subtotal": subtotal,
                "disponibilidade": produto["disponibilidade"],
            }
        )
    return itens


def _totais(itens: list) -> dict:
    subtotal = round(sum(i["subtotal"] for i in itens), 2)
    taxa_servico = round(subtotal * 0.08, 2)
    total = round(subtotal + taxa_servico, 2)
    return {"subtotal": subtotal, "taxa_servico": taxa_servico, "total": total}


@loja_bp.route("", methods=["GET"])
def catalogo():
    busca = request.args.get("busca", "").strip()
    produtos = _buscar_catalogo(busca)
    quantidade_no_carrinho = sum(_carrinho().values())
    return render_template(
        "loja/catalogo.html",
        produtos=produtos,
        busca=busca,
        quantidade_no_carrinho=quantidade_no_carrinho,
    )


@loja_bp.route("/carrinho/adicionar", methods=["POST"])
def adicionar_ao_carrinho():
    produto_id = request.form.get("produto_id", "")
    try:
        quantidade = max(1, int(request.form.get("quantidade", "1")))
    except ValueError:
        quantidade = 1

    carrinho = _carrinho()
    quantidade_pretendida = carrinho.get(produto_id, 0) + quantidade

    try:
        verificacao = requests.post(
            f"{API_URL}/catalogo/verificar-quantidade",
            json={"produto_id": int(produto_id), "quantidade": quantidade_pretendida},
            timeout=5,
        )
    except (requests.exceptions.RequestException, ValueError):
        flash("Não foi possível conectar à loja agora.", "erro")
        return redirect(url_for("loja.catalogo"))

    if verificacao.status_code == 200 and not verificacao.json().get("disponivel", True):
        maximo = verificacao.json().get("maximo_disponivel", 0)
        # Só neste momento — ao tentar selecionar mais do que existe — o
        # cliente sabe o limite exato. O catálogo nunca mostra esse número.
        flash(
            f"Só temos {maximo} unidade(s) disponíveis desse item no momento.",
            "erro",
        )
        return redirect(url_for("loja.catalogo"))
    if verificacao.status_code != 200:
        flash("Não foi possível adicionar este item agora.", "erro")
        return redirect(url_for("loja.catalogo"))

    carrinho[produto_id] = quantidade_pretendida
    _salvar_carrinho(carrinho)
    flash("Item adicionado à sua feira.", "sucesso")
    return redirect(url_for("loja.catalogo"))


@loja_bp.route("/carrinho", methods=["GET"])
def ver_carrinho():
    itens = _itens_do_carrinho()
    totais = _totais(itens)
    return render_template("loja/carrinho.html", itens=itens, **totais)


@loja_bp.route("/carrinho/atualizar/<produto_id>", methods=["POST"])
def atualizar_item(produto_id):
    try:
        quantidade = int(request.form.get("quantidade", "1"))
    except ValueError:
        quantidade = 1

    carrinho = _carrinho()
    if quantidade <= 0:
        carrinho.pop(produto_id, None)
        _salvar_carrinho(carrinho)
        return redirect(url_for("loja.ver_carrinho"))

    try:
        verificacao = requests.post(
            f"{API_URL}/catalogo/verificar-quantidade",
            json={"produto_id": int(produto_id), "quantidade": quantidade},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível conectar à loja agora.", "erro")
        return redirect(url_for("loja.ver_carrinho"))

    if verificacao.status_code == 200 and not verificacao.json().get("disponivel", True):
        maximo = verificacao.json().get("maximo_disponivel", 0)
        flash(f"Só temos {maximo} unidade(s) disponíveis desse item.", "erro")
        quantidade = maximo

    if quantidade <= 0:
        carrinho.pop(produto_id, None)
    else:
        carrinho[produto_id] = quantidade
    _salvar_carrinho(carrinho)
    return redirect(url_for("loja.ver_carrinho"))


@loja_bp.route("/carrinho/remover/<produto_id>", methods=["POST"])
def remover_item(produto_id):
    carrinho = _carrinho()
    carrinho.pop(produto_id, None)
    _salvar_carrinho(carrinho)
    return redirect(url_for("loja.ver_carrinho"))


@loja_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    itens = _itens_do_carrinho()
    if not itens:
        flash("Sua feira está vazia.", "erro")
        return redirect(url_for("loja.catalogo"))
    totais = _totais(itens)

    if request.method == "GET":
        return render_template("loja/checkout.html", itens=itens, **totais)

    nome_cliente = request.form.get("nome_cliente", "").strip()
    telefone_cliente = request.form.get("telefone_cliente", "").strip()
    if not nome_cliente or not telefone_cliente:
        flash("Informe nome e telefone para concluir o pedido.", "erro")
        return render_template("loja/checkout.html", itens=itens, **totais)

    payload = {
        "nome_cliente": nome_cliente,
        "telefone_cliente": telefone_cliente,
        "itens": [
            {"produto_id": int(item["produto_id"]), "quantidade": item["quantidade"]}
            for item in itens
        ],
    }
    try:
        resposta = requests.post(f"{API_URL}/pedidos-online", json=payload, timeout=5)
    except requests.exceptions.RequestException:
        flash("Não foi possível concluir o pedido. Tente novamente.", "erro")
        return render_template("loja/checkout.html", itens=itens, **totais)

    if resposta.status_code != 201:
        mensagem = resposta.json().get("detail", "Não foi possível concluir o pedido.")
        flash(mensagem, "erro")
        return render_template("loja/checkout.html", itens=itens, **totais)

    pedido = resposta.json()
    _salvar_carrinho({})
    return redirect(
        url_for(
            "loja.comprovante",
            numero_pedido=pedido["numero_pedido"],
            telefone=telefone_cliente,
        )
    )


@loja_bp.route("/pedido/<numero_pedido>", methods=["GET"])
def comprovante(numero_pedido):
    telefone = request.args.get("telefone", "")
    pedido = _consultar_pedido(numero_pedido, telefone)
    if not pedido:
        flash("Pedido não encontrado. Use a consulta com o número e o telefone.", "erro")
        return redirect(url_for("loja.consultar"))
    return render_template("loja/comprovante.html", pedido=pedido, telefone=telefone)


@loja_bp.route("/pedido/<numero_pedido>/cancelar", methods=["POST"])
def cancelar(numero_pedido):
    telefone = request.form.get("telefone", "")
    try:
        resposta = requests.post(
            f"{API_URL}/pedidos-online/cancelar",
            json={"numero_pedido": numero_pedido, "telefone_cliente": telefone},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        flash("Não foi possível cancelar agora. Tente novamente.", "erro")
        return redirect(url_for("loja.comprovante", numero_pedido=numero_pedido, telefone=telefone))

    if resposta.status_code != 200:
        mensagem = resposta.json().get("detail", "Não foi possível cancelar o pedido.")
        flash(mensagem, "erro")
    else:
        flash("Pedido cancelado. Confira abaixo o valor que será devolvido.", "sucesso")

    return redirect(url_for("loja.comprovante", numero_pedido=numero_pedido, telefone=telefone))


@loja_bp.route("/consultar", methods=["GET", "POST"])
def consultar():
    if request.method == "GET":
        return render_template("loja/consultar.html")

    numero_pedido = request.form.get("numero_pedido", "").strip()
    telefone = request.form.get("telefone", "").strip()
    pedido = _consultar_pedido(numero_pedido, telefone)
    if not pedido:
        flash("Pedido não encontrado. Confira o número e o telefone.", "erro")
        return render_template("loja/consultar.html")

    return redirect(url_for("loja.comprovante", numero_pedido=numero_pedido, telefone=telefone))


def _consultar_pedido(numero_pedido: str, telefone: str):
    if not numero_pedido or not telefone:
        return None
    try:
        resposta = requests.post(
            f"{API_URL}/pedidos-online/consultar",
            json={"numero_pedido": numero_pedido, "telefone_cliente": telefone},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        return None
    if resposta.status_code != 200:
        return None
    return resposta.json()
