from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app import models
from app.routers import auth, produtos, caixa, vendas, usuarios, pedidos_online


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="PDV Enxuto — API", version="0.2.0", lifespan=ciclo_de_vida)

# A API é chamada pela aplicação Flask (server-to-server) e também, agora,
# pelo navegador do próprio cliente no catálogo público da Feira Online.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(produtos.router)
app.include_router(caixa.router)
app.include_router(vendas.router)
app.include_router(usuarios.router)
app.include_router(pedidos_online.router)


@app.get("/")
def raiz():
    return {"status": "online", "servico": "API do PDV"}
