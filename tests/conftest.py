import os
import sys

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

API_DIR = os.path.join(os.path.dirname(__file__), "..", "api")
sys.path.insert(0, os.path.abspath(API_DIR))

os.environ.setdefault("ADMIN_MASTER_KEY", "senha-admin-teste")

from app.core.database import Base, get_db
from app.core.security import gerar_hash_senha, criar_token_acesso
from app.main import app
from app.models.usuario import Usuario, PerfilUsuario
from app.models.produto import Produto

engine_teste = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


# O SQLite não aplica chaves estrangeiras por padrão (o MySQL de produção
# aplica). Habilitamos aqui para que os testes reflitam o comportamento real.
@event.listens_for(engine_teste, "connect")
def _habilitar_fk_sqlite(conexao_dbapi, _record):
    cursor = conexao_dbapi.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _get_db_teste():
    db = SessionTeste()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_db_teste


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine_teste)
    sessao = SessionTeste()
    yield sessao
    sessao.close()
    Base.metadata.drop_all(bind=engine_teste)


@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def usuario_admin(db_session):
    usuario = Usuario(
        nome="Admin Teste",
        login="admin.teste",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.ADMIN,
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


@pytest.fixture
def usuario_caixa(db_session):
    usuario = Usuario(
        nome="Caixa Teste",
        login="caixa.teste",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.CAIXA,
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


def _token_para(usuario: Usuario) -> str:
    return criar_token_acesso(
        {"sub": usuario.login, "perfil": usuario.perfil.value, "id": usuario.id}
    )


@pytest.fixture
def headers_admin(usuario_admin):
    return {"Authorization": f"Bearer {_token_para(usuario_admin)}"}


@pytest.fixture
def headers_caixa(usuario_caixa):
    return {"Authorization": f"Bearer {_token_para(usuario_caixa)}"}


@pytest.fixture
def produto_refrigerante(db_session):
    produto = Produto(
        codigo="7891000100103",
        nome="Refrigerante Lata 350ml",
        preco="5.50",
        estoque=10,
    )
    db_session.add(produto)
    db_session.commit()
    return produto


@pytest.fixture
def produto_agua(db_session):
    produto = Produto(
        codigo="7891000100202",
        nome="Água Mineral 500ml",
        preco="3.00",
        estoque=1,
    )
    db_session.add(produto)
    db_session.commit()
    return produto
