import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import usuario_atual
from app.models.caixa import Caixa, StatusCaixa
from app.models.produto import Produto
from app.models.venda import Venda, ItemVenda, StatusVenda, FormaPagamento
from app.models.pedido_online import (
    PedidoOnline,
    ItemPedidoOnline,
    StatusPedidoOnline,
    TAXA_SERVICO_PERCENTUAL,
    TAXA_CANCELAMENTO_PERCENTUAL,
)
from app.schemas.produto import ProdutoCatalogoOut
from app.schemas.pedido_online import (
    PedidoOnlineCriar,
    PedidoOnlineConsultar,
    PedidoOnlineOut,
    ItemPedidoOut,
    VerificarQuantidade,
    VerificarQuantidadeResposta,
)

router = APIRouter(tags=["Feira Online"])

LIMITE_POUCAS_UNIDADES = 5


def _duas_casas(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _disponibilidade(estoque: int) -> str:
    if estoque <= 0:
        return "indisponivel"
    if estoque <= LIMITE_POUCAS_UNIDADES:
        return "poucas_unidades"
    return "disponivel"


def _gerar_numero_pedido() -> str:
    return f"F{datetime.utcnow():%y%m%d}{uuid.uuid4().hex[:5].upper()}"


def _montar_pedido_out(pedido: PedidoOnline) -> PedidoOnlineOut:
    itens = [
        ItemPedidoOut(
            id=item.id,
            produto_id=item.produto_id,
            nome_produto=item.produto.nome if item.produto else "—",
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario,
            subtotal=item.subtotal,
        )
        for item in pedido.itens
    ]
    return PedidoOnlineOut(
        id=pedido.id,
        numero_pedido=pedido.numero_pedido,
        nome_cliente=pedido.nome_cliente,
        telefone_cliente=pedido.telefone_cliente,
        status=pedido.status,
        subtotal=pedido.subtotal,
        taxa_servico_percentual=pedido.taxa_servico_percentual,
        taxa_servico_valor=pedido.taxa_servico_valor,
        valor_total=pedido.valor_total,
        taxa_cancelamento_percentual=pedido.taxa_cancelamento_percentual,
        taxa_cancelamento_valor=pedido.taxa_cancelamento_valor,
        valor_reembolsado=pedido.valor_reembolsado,
        criado_em=pedido.criado_em,
        retirado_em=pedido.retirado_em,
        cancelado_em=pedido.cancelado_em,
        itens=itens,
    )


def _buscar_pedido_ou_404(db: Session, numero_pedido: str, telefone_cliente: str) -> PedidoOnline:
    pedido = (
        db.query(PedidoOnline)
        .filter(PedidoOnline.numero_pedido == numero_pedido.strip().upper())
        .first()
    )
    # Mesma mensagem para "não existe" e "telefone não confere": evita que
    # alguém descubra, por tentativa e erro, se um código de pedido existe.
    if not pedido or pedido.telefone_cliente != telefone_cliente.strip():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado. Confira o número e o telefone informado.",
        )
    return pedido


# ---------------------------------------------------------------------------
# Catálogo público — nenhuma rota abaixo exige login. Só mostra produtos
# ativos e marcados pelo admin como disponíveis na loja online, e nunca expõe
# o estoque exato (só uma faixa de disponibilidade).
# ---------------------------------------------------------------------------


@router.get("/catalogo", response_model=list[ProdutoCatalogoOut])
def listar_catalogo(
    busca: str = "",
    skip: int = 0,
    limit: int = Query(60, le=200),
    db: Session = Depends(get_db),
):
    consulta = db.query(Produto).filter(
        Produto.ativo.is_(True), Produto.disponivel_loja.is_(True)
    )
    if busca:
        consulta = consulta.filter(Produto.nome.ilike(f"%{busca}%"))

    produtos = consulta.order_by(Produto.nome).offset(skip).limit(limit).all()
    return [
        ProdutoCatalogoOut(
            id=p.id,
            codigo=p.codigo,
            nome=p.nome,
            preco=p.preco,
            disponibilidade=_disponibilidade(p.estoque),
        )
        for p in produtos
    ]


@router.post("/catalogo/verificar-quantidade", response_model=VerificarQuantidadeResposta)
def verificar_quantidade(dados: VerificarQuantidade, db: Session = Depends(get_db)):
    produto = (
        db.query(Produto)
        .filter(
            Produto.id == dados.produto_id,
            Produto.ativo.is_(True),
            Produto.disponivel_loja.is_(True),
        )
        .first()
    )
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado na loja."
        )
    if produto.estoque < dados.quantidade:
        return VerificarQuantidadeResposta(disponivel=False, maximo_disponivel=produto.estoque)
    return VerificarQuantidadeResposta(disponivel=True)


# ---------------------------------------------------------------------------
# Pedido — criação, consulta e cancelamento são públicos (o cliente não tem
# login; a "senha" dele é o par número do pedido + telefone).
# ---------------------------------------------------------------------------


@router.post("/pedidos-online", response_model=PedidoOnlineOut, status_code=status.HTTP_201_CREATED)
def criar_pedido(dados: PedidoOnlineCriar, db: Session = Depends(get_db)):
    itens_para_salvar = []
    subtotal = Decimal("0")

    for entrada in dados.itens:
        produto = (
            db.query(Produto)
            .filter(
                Produto.id == entrada.produto_id,
                Produto.ativo.is_(True),
                Produto.disponivel_loja.is_(True),
            )
            .first()
        )
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto {entrada.produto_id} não encontrado na loja.",
            )
        if produto.estoque < entrada.quantidade:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Quantidade indisponível para '{produto.nome}'. "
                    f"Máximo disponível no momento: {produto.estoque}."
                ),
            )
        item_subtotal = _duas_casas(produto.preco * entrada.quantidade)
        subtotal += item_subtotal
        itens_para_salvar.append((produto, entrada.quantidade, item_subtotal))

    taxa_servico_valor = _duas_casas(subtotal * Decimal(TAXA_SERVICO_PERCENTUAL) / Decimal(100))
    valor_total = _duas_casas(subtotal + taxa_servico_valor)

    pedido = PedidoOnline(
        numero_pedido=_gerar_numero_pedido(),
        nome_cliente=dados.nome_cliente.strip(),
        telefone_cliente=dados.telefone_cliente.strip(),
        status=StatusPedidoOnline.AGUARDANDO_RETIRADA,
        subtotal=subtotal,
        taxa_servico_percentual=Decimal(TAXA_SERVICO_PERCENTUAL),
        taxa_servico_valor=taxa_servico_valor,
        valor_total=valor_total,
    )
    db.add(pedido)
    db.flush()

    # Os produtos já saem do estoque disponível no momento do pagamento —
    # é o que garante que o funcionário só monte feiras com itens de fato
    # reservados, e evita vender duas vezes a mesma última unidade.
    for produto, quantidade, item_subtotal in itens_para_salvar:
        produto.estoque -= quantidade
        db.add(
            ItemPedidoOnline(
                pedido_id=pedido.id,
                produto_id=produto.id,
                quantidade=quantidade,
                preco_unitario=produto.preco,
                subtotal=item_subtotal,
            )
        )

    db.commit()
    db.refresh(pedido)
    return _montar_pedido_out(pedido)


@router.post("/pedidos-online/consultar", response_model=PedidoOnlineOut)
def consultar_pedido(dados: PedidoOnlineConsultar, db: Session = Depends(get_db)):
    pedido = _buscar_pedido_ou_404(db, dados.numero_pedido, dados.telefone_cliente)
    return _montar_pedido_out(pedido)


@router.post("/pedidos-online/cancelar", response_model=PedidoOnlineOut)
def cancelar_pedido(dados: PedidoOnlineConsultar, db: Session = Depends(get_db)):
    pedido = _buscar_pedido_ou_404(db, dados.numero_pedido, dados.telefone_cliente)

    if pedido.status != StatusPedidoOnline.AGUARDANDO_RETIRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este pedido não pode mais ser cancelado (já foi retirado ou já está cancelado).",
        )

    # Os itens ainda não foram retirados, então voltam para o estoque —
    # mas a taxa de cancelamento de 15% sobre o valor final é retida.
    for item in pedido.itens:
        if item.produto:
            item.produto.estoque += item.quantidade

    taxa_cancelamento_valor = _duas_casas(
        pedido.valor_total * Decimal(TAXA_CANCELAMENTO_PERCENTUAL) / Decimal(100)
    )
    pedido.taxa_cancelamento_percentual = Decimal(TAXA_CANCELAMENTO_PERCENTUAL)
    pedido.taxa_cancelamento_valor = taxa_cancelamento_valor
    pedido.valor_reembolsado = _duas_casas(pedido.valor_total - taxa_cancelamento_valor)
    pedido.status = StatusPedidoOnline.CANCELADO
    pedido.cancelado_em = datetime.utcnow()

    db.commit()
    db.refresh(pedido)
    return _montar_pedido_out(pedido)


# ---------------------------------------------------------------------------
# Operação de loja — exige um funcionário autenticado (operador de caixa ou
# admin) para conferir e liberar a retirada.
# ---------------------------------------------------------------------------


@router.get("/pedidos-online", response_model=list[PedidoOnlineOut])
def listar_pedidos_online(
    status_filtro: StatusPedidoOnline = StatusPedidoOnline.AGUARDANDO_RETIRADA,
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _usuario: dict = Depends(usuario_atual),
):
    pedidos = (
        db.query(PedidoOnline)
        .filter(PedidoOnline.status == status_filtro)
        .order_by(PedidoOnline.criado_em.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_montar_pedido_out(p) for p in pedidos]


@router.post("/pedidos-online/{pedido_id}/retirar", response_model=PedidoOnlineOut)
def confirmar_retirada(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: dict = Depends(usuario_atual),
):
    pedido = db.query(PedidoOnline).filter(PedidoOnline.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")
    if pedido.status != StatusPedidoOnline.AGUARDANDO_RETIRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este pedido já foi retirado ou está cancelado.",
        )

    caixa = (
        db.query(Caixa)
        .filter(Caixa.usuario_id == usuario["id"], Caixa.status == StatusCaixa.ABERTO)
        .first()
    )
    if not caixa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Abra o caixa antes de confirmar retiradas — a retirada gera uma venda no seu turno.",
        )

    # Gera a venda correspondente para que a feira online entre no
    # faturamento e no fechamento de caixa, igual a qualquer outra venda.
    # O estoque NÃO é debitado de novo aqui: já saiu no momento do pagamento.
    venda = Venda(
        caixa_id=caixa.id,
        usuario_id=usuario["id"],
        forma_pagamento=FormaPagamento.ONLINE,
        status=StatusVenda.CONCLUIDA,
        valor_total=pedido.valor_total,
    )
    db.add(venda)
    db.flush()

    for item in pedido.itens:
        db.add(
            ItemVenda(
                venda_id=venda.id,
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                subtotal=item.subtotal,
            )
        )

    pedido.status = StatusPedidoOnline.RETIRADO
    pedido.retirado_em = datetime.utcnow()
    pedido.venda_id = venda.id

    db.commit()
    db.refresh(pedido)
    return _montar_pedido_out(pedido)
