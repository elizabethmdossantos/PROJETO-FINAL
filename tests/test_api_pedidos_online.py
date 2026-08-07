def test_catalogo_nao_expoe_estoque_exato(cliente, produto_refrigerante):
    resposta = cliente.get("/catalogo")
    assert resposta.status_code == 200
    item = resposta.json()[0]
    assert "estoque" not in item
    assert item["disponibilidade"] in {"disponivel", "poucas_unidades", "indisponivel"}


def test_catalogo_nao_lista_produto_inativo(cliente, produto_refrigerante, db_session):
    produto_refrigerante.ativo = False
    db_session.commit()
    resposta = cliente.get("/catalogo")
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_verificar_quantidade_acima_do_estoque_informa_maximo(cliente, produto_agua):
    resposta = cliente.post(
        "/catalogo/verificar-quantidade",
        json={"produto_id": produto_agua.id, "quantidade": 5},
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["disponivel"] is False
    assert dados["maximo_disponivel"] == 1


def test_criar_pedido_com_sucesso_debita_estoque_e_calcula_taxa(cliente, produto_refrigerante):
    payload = {
        "nome_cliente": "Maria Cliente",
        "telefone_cliente": "82999990000",
        "itens": [{"produto_id": produto_refrigerante.id, "quantidade": 2}],
    }
    resposta = cliente.post("/pedidos-online", json=payload)
    assert resposta.status_code == 201
    dados = resposta.json()

    assert dados["subtotal"] == "11.00"
    assert dados["taxa_servico_valor"] == "0.88"
    assert dados["valor_total"] == "11.88"
    assert dados["numero_pedido"].startswith("F")
    assert dados["status"] == "aguardando_retirada"

    catalogo = cliente.get("/catalogo").json()
    assert catalogo[0]["disponibilidade"] == "disponivel"  # 10 - 2 = 8, ainda ok


def test_criar_pedido_com_estoque_insuficiente_e_recusado(cliente, produto_agua):
    payload = {
        "nome_cliente": "João Cliente",
        "telefone_cliente": "82999991111",
        "itens": [{"produto_id": produto_agua.id, "quantidade": 3}],
    }
    resposta = cliente.post("/pedidos-online", json=payload)
    assert resposta.status_code == 409


def test_consultar_pedido_com_telefone_errado_nao_encontra(cliente, produto_refrigerante):
    payload = {
        "nome_cliente": "Ana Cliente",
        "telefone_cliente": "82988887777",
        "itens": [{"produto_id": produto_refrigerante.id, "quantidade": 1}],
    }
    criado = cliente.post("/pedidos-online", json=payload).json()

    resposta = cliente.post(
        "/pedidos-online/consultar",
        json={"numero_pedido": criado["numero_pedido"], "telefone_cliente": "0000"},
    )
    assert resposta.status_code == 404


def test_cancelar_pedido_devolve_estoque_e_cobra_taxa(cliente, produto_refrigerante, db_session):
    payload = {
        "nome_cliente": "Carlos Cliente",
        "telefone_cliente": "82977776666",
        "itens": [{"produto_id": produto_refrigerante.id, "quantidade": 2}],
    }
    criado = cliente.post("/pedidos-online", json=payload).json()

    resposta = cliente.post(
        "/pedidos-online/cancelar",
        json={
            "numero_pedido": criado["numero_pedido"],
            "telefone_cliente": payload["telefone_cliente"],
        },
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["status"] == "cancelado"
    assert dados["taxa_cancelamento_valor"] == "1.78"  # 15% de 11.88
    assert dados["valor_reembolsado"] == "10.10"

    db_session.refresh(produto_refrigerante)
    assert produto_refrigerante.estoque == 10  # estoque original devolvido


def test_cancelar_pedido_duas_vezes_e_recusado(cliente, produto_refrigerante):
    payload = {
        "nome_cliente": "Bia Cliente",
        "telefone_cliente": "82966665555",
        "itens": [{"produto_id": produto_refrigerante.id, "quantidade": 1}],
    }
    criado = cliente.post("/pedidos-online", json=payload).json()
    consulta = {
        "numero_pedido": criado["numero_pedido"],
        "telefone_cliente": payload["telefone_cliente"],
    }
    cliente.post("/pedidos-online/cancelar", json=consulta)
    resposta = cliente.post("/pedidos-online/cancelar", json=consulta)
    assert resposta.status_code == 409


def test_listar_pedidos_online_exige_login(cliente):
    resposta = cliente.get("/pedidos-online")
    assert resposta.status_code == 401


def test_retirar_pedido_sem_caixa_aberto_e_recusado(cliente, headers_caixa, produto_refrigerante):
    payload = {
        "nome_cliente": "Duda Cliente",
        "telefone_cliente": "82955554444",
        "itens": [{"produto_id": produto_refrigerante.id, "quantidade": 1}],
    }
    criado = cliente.post("/pedidos-online", json=payload).json()

    resposta = cliente.post(f"/pedidos-online/{criado['id']}/retirar", headers=headers_caixa)
    assert resposta.status_code == 409


def test_retirar_pedido_gera_venda_no_caixa_aberto(cliente, headers_caixa, produto_refrigerante):
    cliente.post(
        "/caixa/abrir", json={"valor_abertura": "50.00"}, headers=headers_caixa
    )

    payload = {
        "nome_cliente": "Duda Cliente",
        "telefone_cliente": "82955554444",
        "itens": [{"produto_id": produto_refrigerante.id, "quantidade": 1}],
    }
    criado = cliente.post("/pedidos-online", json=payload).json()

    resposta = cliente.post(f"/pedidos-online/{criado['id']}/retirar", headers=headers_caixa)
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "retirado"

    fechamento = cliente.post(
        "/caixa/fechar", json={"valor_fechamento": "50.00"}, headers=headers_caixa
    ).json()
    assert fechamento["quantidade_vendas"] == 1
    assert fechamento["total_vendas"] == "5.94"
