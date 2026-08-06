def test_listar_usuarios_sem_token_e_recusado(cliente, db_session, usuario_admin):
    resposta = cliente.get("/usuarios")
    assert resposta.status_code == 401


def test_criar_usuario_sem_token_e_recusado(cliente, db_session, usuario_admin):
    payload = {
        "nome": "Invasor",
        "login": "invasor",
        "senha": "1234",
        "perfil": "admin",
    }
    resposta = cliente.post("/usuarios", json=payload)
    assert resposta.status_code == 401
    # Garante que o usuário realmente não foi criado.
    assert (
        cliente.get(
            "/usuarios",
        ).status_code
        == 401
    )


def test_operador_comum_nao_pode_gerenciar_usuarios(cliente, headers_caixa):
    resposta = cliente.get("/usuarios", headers=headers_caixa)
    assert resposta.status_code == 403


def test_admin_lista_usuarios(cliente, headers_admin, usuario_admin):
    resposta = cliente.get("/usuarios", headers=headers_admin)
    assert resposta.status_code == 200
    logins = [u["login"] for u in resposta.json()]
    assert "admin.teste" in logins


def test_admin_cria_usuario_com_sucesso(cliente, headers_admin):
    payload = {
        "nome": "Novo Operador",
        "login": "novo.operador",
        "senha": "1234",
        "perfil": "caixa",
    }
    resposta = cliente.post("/usuarios", json=payload, headers=headers_admin)
    assert resposta.status_code == 201
    assert "senha" not in resposta.json()
    assert "senha_hash" not in resposta.json()


def test_admin_nao_cria_usuario_com_login_duplicado(cliente, headers_admin, usuario_admin):
    payload = {
        "nome": "Duplicado",
        "login": usuario_admin.login,
        "senha": "1234",
        "perfil": "caixa",
    }
    resposta = cliente.post("/usuarios", json=payload, headers=headers_admin)
    assert resposta.status_code == 409


def test_admin_atualiza_perfil_de_usuario(cliente, headers_admin, usuario_caixa):
    resposta = cliente.put(
        f"/usuarios/{usuario_caixa.id}",
        json={"perfil": "admin"},
        headers=headers_admin,
    )
    assert resposta.status_code == 200
    assert resposta.json()["perfil"] == "admin"


def test_nao_pode_excluir_usuario_admin_padrao(cliente, headers_admin, db_session):
    from app.core.security import gerar_hash_senha
    from app.models.usuario import Usuario, PerfilUsuario

    admin_padrao = Usuario(
        nome="Administrador",
        login="admin",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.ADMIN,
    )
    db_session.add(admin_padrao)
    db_session.commit()

    resposta = cliente.delete(f"/usuarios/{admin_padrao.id}", headers=headers_admin)
    assert resposta.status_code == 400


def test_excluir_usuario_com_caixa_vinculado_retorna_conflito(
    cliente, headers_admin, usuario_caixa, db_session
):
    from app.models.caixa import Caixa, StatusCaixa

    caixa = Caixa(
        usuario_id=usuario_caixa.id,
        status=StatusCaixa.ABERTO,
        valor_abertura="50.00",
    )
    db_session.add(caixa)
    db_session.commit()

    resposta = cliente.delete(f"/usuarios/{usuario_caixa.id}", headers=headers_admin)
    assert resposta.status_code == 409


def test_excluir_usuario_sem_vinculos_funciona(cliente, headers_admin, usuario_caixa):
    resposta = cliente.delete(f"/usuarios/{usuario_caixa.id}", headers=headers_admin)
    assert resposta.status_code == 204
