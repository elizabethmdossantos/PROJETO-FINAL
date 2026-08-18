def test_admin_cria_produto_com_sucesso(cliente, headers_admin):
    resposta = cliente.post(
        "/produtos",
        json={"codigo": "1111111111111", "nome": "Item Teste", "preco": "9.90", "estoque": 15},
        headers=headers_admin,
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["codigo"] == "1111111111111"
    assert corpo["ativo"] is True


def test_operador_nao_pode_criar_produto(cliente, headers_caixa):
    resposta = cliente.post(
        "/produtos",
        json={"codigo": "2222222222222", "nome": "Item Proibido", "preco": "1.00", "estoque": 1},
        headers=headers_caixa,
    )
    assert resposta.status_code == 403


def test_nao_pode_criar_produto_com_codigo_duplicado(cliente, headers_admin, produto_refrigerante):
    resposta = cliente.post(
        "/produtos",
        json={
            "codigo": "7891000100103",
            "nome": "Duplicado",
            "preco": "1.00",
            "estoque": 1,
        },
        headers=headers_admin,
    )
    assert resposta.status_code == 409


def test_busca_por_codigo_ignora_produto_inativo(cliente, headers_admin, produto_refrigerante):
    cliente.patch(
        f"/produtos/{produto_refrigerante.id}",
        json={"ativo": False},
        headers=headers_admin,
    )
    resposta = cliente.get(
        f"/produtos/codigo/{produto_refrigerante.codigo}", headers=headers_admin
    )
    assert resposta.status_code == 404


def test_admin_atualiza_preco_e_estoque(cliente, headers_admin, produto_refrigerante):
    resposta = cliente.patch(
        f"/produtos/{produto_refrigerante.id}",
        json={"preco": "6.00", "estoque": 200},
        headers=headers_admin,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["preco"] == "6.00"
    assert corpo["estoque"] == 200


def test_operador_nao_pode_listar_estoque_completo(cliente, headers_caixa):
    resposta = cliente.get("/produtos", headers=headers_caixa)
    assert resposta.status_code == 403


def test_admin_lista_apenas_ativos_por_padrao(cliente, headers_admin, produto_refrigerante, produto_agua):
    cliente.patch(
        f"/produtos/{produto_agua.id}", json={"ativo": False}, headers=headers_admin
    )
    resposta = cliente.get("/produtos", headers=headers_admin)
    codigos = [p["codigo"] for p in resposta.json()]
    assert produto_refrigerante.codigo in codigos
    assert produto_agua.codigo not in codigos
