def test_abrir_caixa_com_sucesso(cliente, headers_caixa):
    resposta = cliente.post(
        "/caixa/abrir",
        json={"valor_abertura": "100.00", "observacoes": "Troco inicial"},
        headers=headers_caixa,
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "aberto"
    assert corpo["valor_abertura"] == "100.00"


def test_nao_pode_abrir_dois_caixas_ao_mesmo_tempo(cliente, headers_caixa):
    cliente.post("/caixa/abrir", json={"valor_abertura": "100.00"}, headers=headers_caixa)
    resposta = cliente.post(
        "/caixa/abrir", json={"valor_abertura": "50.00"}, headers=headers_caixa
    )
    assert resposta.status_code == 409


def test_caixa_atual_retorna_o_turno_aberto(cliente, headers_caixa):
    cliente.post("/caixa/abrir", json={"valor_abertura": "100.00"}, headers=headers_caixa)
    resposta = cliente.get("/caixa/atual", headers=headers_caixa)
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "aberto"


def test_caixa_atual_sem_turno_aberto_retorna_404(cliente, headers_caixa):
    resposta = cliente.get("/caixa/atual", headers=headers_caixa)
    assert resposta.status_code == 404


def test_fechar_caixa_sem_vendas_zera_o_resumo(cliente, headers_caixa):
    cliente.post("/caixa/abrir", json={"valor_abertura": "100.00"}, headers=headers_caixa)
    resposta = cliente.post(
        "/caixa/fechar", json={"valor_fechamento": "100.00"}, headers=headers_caixa
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "fechado"
    assert corpo["quantidade_vendas"] == 0
    assert corpo["total_vendas"] == "0"


def test_fechar_caixa_sem_turno_aberto_retorna_404(cliente, headers_caixa):
    resposta = cliente.post(
        "/caixa/fechar", json={"valor_fechamento": "0"}, headers=headers_caixa
    )
    assert resposta.status_code == 404


def test_operador_nao_acessa_historico_de_todos_os_caixas(cliente, headers_caixa):
    resposta = cliente.get("/caixa", headers=headers_caixa)
    assert resposta.status_code == 403


def test_admin_acessa_historico_de_caixas(cliente, headers_caixa, headers_admin):
    cliente.post("/caixa/abrir", json={"valor_abertura": "100.00"}, headers=headers_caixa)
    resposta = cliente.get("/caixa", headers=headers_admin)
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_fechar_caixa_nao_soma_venda_cancelada_no_resumo(
    cliente, headers_caixa, headers_admin, produto_refrigerante
):
    cliente.post("/caixa/abrir", json={"valor_abertura": "100.00"}, headers=headers_caixa)
    venda = cliente.post(
        "/vendas",
        json={
            "forma_pagamento": "pix",
            "itens": [{"codigo_produto": "7891000100103", "quantidade": 2}],
        },
        headers=headers_caixa,
    ).json()

    cliente.post(f"/vendas/{venda['id']}/cancelar", headers=headers_admin)

    resposta = cliente.post(
        "/caixa/fechar", json={"valor_fechamento": "100.00"}, headers=headers_caixa
    )
    corpo = resposta.json()
    assert corpo["quantidade_vendas"] == 0
    assert corpo["total_vendas"] == "0"
