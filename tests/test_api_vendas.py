def _abrir_caixa(cliente, headers):
    resposta = cliente.post(
        "/caixa/abrir", json={"valor_abertura": "100.00"}, headers=headers
    )
    assert resposta.status_code == 201


def test_venda_com_sucesso_debita_estoque_e_calcula_total(
    cliente, headers_caixa, produto_refrigerante
):
    _abrir_caixa(cliente, headers_caixa)

    resposta = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 3}],
        },
        headers=headers_caixa,
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["valor_total"] == "16.50"
    assert corpo["forma_pagamento"] == "pix"
    assert len(corpo["itens"]) == 1

    busca = cliente.get("/produtos/codigo/7891000100103", headers=headers_caixa)
    assert busca.json()["estoque"] == 7


def test_venda_com_varios_itens_soma_o_total_corretamente(
    cliente, headers_caixa, produto_refrigerante, produto_agua
):
    _abrir_caixa(cliente, headers_caixa)

    resposta = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "cartao",
            "itens": [
                {"codigo_produto": "7891000100103", "quantidade": 2},
                {"codigo_produto": "7891000100202", "quantidade": 1},
            ],
        },
        headers=headers_caixa,
    )
    assert resposta.status_code == 201
    assert resposta.json()["valor_total"] == "14.00"


def test_venda_sem_caixa_aberto_e_recusada(cliente, headers_caixa, produto_refrigerante):
    resposta = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 1}],
        },
        headers=headers_caixa,
    )
    assert resposta.status_code == 409


def test_venda_com_codigo_de_produto_inexistente(cliente, headers_caixa):
    _abrir_caixa(cliente, headers_caixa)
    resposta = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "0000000000000", "quantidade": 1}],
        },
        headers=headers_caixa,
    )
    assert resposta.status_code == 404


def test_venda_com_estoque_insuficiente_e_recusada_e_nao_altera_estoque(
    cliente, headers_caixa, produto_agua
):
    _abrir_caixa(cliente, headers_caixa)
    resposta = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "vale_refeicao",
            "itens": [{"codigo_produto": "7891000100202", "quantidade": 5}],
        },
        headers=headers_caixa,
    )
    assert resposta.status_code == 409

    busca = cliente.get("/produtos/codigo/7891000100202", headers=headers_caixa)
    assert busca.json()["estoque"] == 1


def test_operador_ve_apenas_as_proprias_vendas(
    cliente, headers_caixa, headers_admin, produto_refrigerante
):
    _abrir_caixa(cliente, headers_caixa)
    cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 1}],
        },
        headers=headers_caixa,
    )

    minhas = cliente.get("/vendas/minhas", headers=headers_caixa)
    assert minhas.status_code == 200
    assert len(minhas.json()) == 1

    proibido = cliente.get("/vendas", headers=headers_caixa)
    assert proibido.status_code == 403


def test_admin_ve_todas_as_vendas_com_nome_do_operador(
    cliente, headers_caixa, headers_admin, produto_refrigerante
):
    _abrir_caixa(cliente, headers_caixa)
    cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "cartao",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 1}],
        },
        headers=headers_caixa,
    )

    resposta = cliente.get("/vendas", headers=headers_admin)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["nome_operador"] == "Caixa Teste"
    assert corpo[0]["itens"][0]["nome_produto"] == "Refrigerante Lata 350ml"


def test_cancelar_venda_devolve_estoque_e_muda_status(
    cliente, headers_caixa, headers_admin, produto_refrigerante
):
    _abrir_caixa(cliente, headers_caixa)
    venda = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 4}],
        },
        headers=headers_caixa,
    ).json()

    busca_antes = cliente.get("/produtos/codigo/7891000100103", headers=headers_caixa)
    assert busca_antes.json()["estoque"] == 6

    resposta = cliente.post(f"/vendas/{venda['id']}/cancelar", headers=headers_admin)
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelada"

    busca_depois = cliente.get("/produtos/codigo/7891000100103", headers=headers_caixa)
    assert busca_depois.json()["estoque"] == 10


def test_cancelar_venda_duas_vezes_e_recusado(
    cliente, headers_caixa, headers_admin, produto_refrigerante
):
    _abrir_caixa(cliente, headers_caixa)
    venda = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 1}],
        },
        headers=headers_caixa,
    ).json()

    cliente.post(f"/vendas/{venda['id']}/cancelar", headers=headers_admin)
    resposta = cliente.post(f"/vendas/{venda['id']}/cancelar", headers=headers_admin)
    assert resposta.status_code == 409


def test_operador_nao_pode_cancelar_venda(
    cliente, headers_caixa, produto_refrigerante
):
    _abrir_caixa(cliente, headers_caixa)
    venda = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 1}],
        },
        headers=headers_caixa,
    ).json()

    resposta = cliente.post(f"/vendas/{venda['id']}/cancelar", headers=headers_caixa)
    assert resposta.status_code == 403


def test_filtro_por_periodo_exclui_vendas_fora_do_intervalo(
    cliente, headers_caixa, headers_admin, produto_refrigerante
):
    _abrir_caixa(cliente, headers_caixa)
    cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 1}],
        },
        headers=headers_caixa,
    )

    from datetime import date, timedelta

    ontem = (date.today() - timedelta(days=1)).isoformat()
    anteontem = (date.today() - timedelta(days=2)).isoformat()

    resposta_fora = cliente.get(
        "/vendas",
        params={"data_inicio": anteontem, "data_fim": ontem},
        headers=headers_admin,
    )
    assert resposta_fora.status_code == 200
    assert resposta_fora.json() == []

    resposta_hoje = cliente.get(
        "/vendas",
        params={"data_inicio": date.today().isoformat()},
        headers=headers_admin,
    )
    assert resposta_hoje.status_code == 200
    assert len(resposta_hoje.json()) == 1
