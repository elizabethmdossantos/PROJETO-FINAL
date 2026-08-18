import importlib
from pathlib import Path


def test_login_caixa_com_credenciais_corretas(cliente, usuario_caixa):
    resposta = cliente.post(
        "/auth/login",
        json={
            "login": "caixa.teste",
            "senha": "senha123",
            "perfil_solicitado": "caixa",
        },
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["usuario"]["perfil"] == "caixa"
    assert "access_token" in corpo


def test_login_admin_com_senha_administrativa_correta(cliente, usuario_admin, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_MASTER_KEY", "senha-admin-teste")
    resposta = cliente.post(
        "/auth/login",
        json={
            "login": "admin.teste",
            "senha": "senha123",
            "perfil_solicitado": "admin",
            "senha_admin": "senha-admin-teste",
        },
    )
    assert resposta.status_code == 200
    assert resposta.json()["usuario"]["perfil"] == "admin"


def test_login_admin_sem_segunda_senha_e_bloqueado(cliente, usuario_admin, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_MASTER_KEY", "senha-admin-teste")
    resposta = cliente.post(
        "/auth/login",
        json={
            "login": "admin.teste",
            "senha": "senha123",
            "perfil_solicitado": "admin",
            "senha_admin": "senha-errada",
        },
    )
    assert resposta.status_code == 401


def test_caixa_nao_pode_entrar_marcando_administrador(cliente, usuario_caixa, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_MASTER_KEY", "senha-admin-teste")
    resposta = cliente.post(
        "/auth/login",
        json={
            "login": "caixa.teste",
            "senha": "senha123",
            "perfil_solicitado": "admin",
            "senha_admin": "senha-admin-teste",
        },
    )
    assert resposta.status_code == 403


def test_login_com_senha_incorreta(cliente, usuario_caixa):
    resposta = cliente.post(
        "/auth/login",
        json={
            "login": "caixa.teste",
            "senha": "senha-errada",
            "perfil_solicitado": "caixa",
        },
    )
    assert resposta.status_code == 401


def test_config_carrega_admin_master_key_do_dotenv_da_api(monkeypatch):
    api_dir = Path(__file__).resolve().parent.parent / "api"
    env_path = api_dir / ".env"
    backup = env_path.read_text(encoding="utf-8") if env_path.exists() else None

    try:
        env_path.write_text("ADMIN_MASTER_KEY=senha-do-dotenv\n", encoding="utf-8")
        monkeypatch.delenv("ADMIN_MASTER_KEY", raising=False)
        monkeypatch.chdir(api_dir.parent)

        import app.core.config as config

        importlib.reload(config)
        assert config.settings.ADMIN_MASTER_KEY == "senha-do-dotenv"
    finally:
        if backup is None:
            env_path.unlink(missing_ok=True)
        else:
            env_path.write_text(backup, encoding="utf-8")

        import app.core.config as config

        importlib.reload(config)
