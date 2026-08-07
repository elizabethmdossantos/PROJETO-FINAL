from app.core.database import SessionLocal, Base, engine
from app.core.security import gerar_hash_senha
from app.models.usuario import Usuario, PerfilUsuario

Base.metadata.create_all(bind=engine)

db = SessionLocal()

usuarios_teste = [
    {"nome": "Administradora Geral", "login": "admin", "senha": "admin123", "perfil": PerfilUsuario.ADMIN},
    {"nome": "Operador de Caixa", "login": "caixa1", "senha": "caixa123", "perfil": PerfilUsuario.CAIXA},
]

for dados in usuarios_teste:
    existente = db.query(Usuario).filter(Usuario.login == dados["login"]).first()
    if existente:
        print(f"Usuário '{dados['login']}' já existe, pulando.")
        continue

    usuario = Usuario(
        nome=dados["nome"],
        login=dados["login"],
        senha_hash=gerar_hash_senha(dados["senha"]),
        perfil=dados["perfil"],
    )
    db.add(usuario)
    print(f"Usuário '{dados['login']}' criado com senha '{dados['senha']}'.")

db.commit()
db.close()

print("\nLembre-se: a senha ADMINISTRATIVA extra (2º fator) é a que está em")
print("ADMIN_MASTER_KEY no arquivo .env — não é a senha do usuário 'admin'.")
