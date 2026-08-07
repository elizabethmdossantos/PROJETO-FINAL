from app.core.database import SessionLocal, Base, engine
from app.models.produto import Produto

Base.metadata.create_all(bind=engine)

db = SessionLocal()

produtos_teste = [
    {"codigo": "7891000100103", "nome": "Refrigerante Lata 350ml", "preco": 5.50, "estoque": 120},
    {"codigo": "7891000100202", "nome": "Água Mineral 500ml", "preco": 3.00, "estoque": 200},
    {"codigo": "7891000100301", "nome": "Salgado Assado", "preco": 8.00, "estoque": 50},
    {"codigo": "7891000100400", "nome": "Chocolate ao Leite 90g", "preco": 7.90, "estoque": 80},
    {"codigo": "7891000100509", "nome": "Café Expresso", "preco": 4.50, "estoque": 999},
]

for dados in produtos_teste:
    existente = db.query(Produto).filter(Produto.codigo == dados["codigo"]).first()
    if existente:
        print(f"Produto '{dados['codigo']}' já existe, pulando.")
        continue

    produto = Produto(**dados)
    db.add(produto)
    print(f"Produto '{dados['nome']}' ({dados['codigo']}) criado.")

db.commit()
db.close()
