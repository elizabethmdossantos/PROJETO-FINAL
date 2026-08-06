from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import usuario_atual, exigir_admin
from app.models.caixa import Caixa, StatusCaixa
from app.models.produto import Produto
from app.models.venda import Venda, ItemVenda, StatusVenda
from app.models.usuario import Usuario
from app.schemas.venda import VendaCriar, VendaOut, VendaDetalhada, ItemVendaDetalhado

router = APIRouter(prefix="/vendas", tags=["Vendas"])


def _caixa_aberto_do_usuario(db: Session, usuario_id: int) -> Caixa:
    caixa = (
        db.query(Caixa)
        .filter(Caixa.usuario_id == usuario_id, Caixa.status == StatusCaixa.ABERTO)
        .first()
    )
    if not caixa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Abra o caixa antes de registrar vendas.",
        )
    return caixa


def _montar_venda_detalhada(db: Session, venda: Venda) -> VendaDetalhada:
    operador = db.query(Usuario).filter(Usuario.id == venda.usuario_id).first()
    itens_detalhados = [
        ItemVendaDetalhado(
            id=item.id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario,
            subtotal=item.subtotal,
            codigo_produto=item.produto.codigo,
            nome_produto=item.produto.nome,
        )
        for item in venda.itens
    ]
    return VendaDetalhada(
        id=venda.id,
        caixa_id=venda.caixa_id,
        usuario_id=venda.usuario_id,
        nome_operador=operador.nome if operador else "—",
        forma_pagamento=venda.forma_pagamento,
        status=venda.status,
        valor_total=venda.valor_total,
        criado_em=venda.criado_em,
        itens=itens_detalhados,
    )


@router.post("", response_model=VendaOut, status_code=status.HTTP_201_CREATED)
def registrar_venda(
    dados: VendaCriar,
    db: Session = Depends(get_db),
    usuario: dict = Depends(usuario_atual),
):
    caixa = _caixa_aberto_do_usuario(db, usuario["id"])

    itens_para_salvar = []
    valor_total = Decimal("0")

    for entrada in dados.itens:
        produto = (
            db.query(Produto)
            .filter(Produto.codigo == entrada.codigo_produto, Produto.ativo.is_(True))
            .first()
        )
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com código '{entrada.codigo_produto}' não encontrado.",
            )
        if produto.estoque < entrada.quantidade:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Estoque insuficiente para '{produto.nome}' "
                    f"(disponível: {produto.estoque}, pedido: {entrada.quantidade})."
                ),
            )

        subtotal = produto.preco * entrada.quantidade
        valor_total += subtotal
        itens_para_salvar.append((produto, entrada.quantidade, subtotal))

    venda = Venda(
        caixa_id=caixa.id,
        usuario_id=usuario["id"],
        forma_pagamento=dados.forma_pagamento,
        status=StatusVenda.CONCLUIDA,
        valor_total=valor_total,
    )
    db.add(venda)
    db.flush()

    for produto, quantidade, subtotal in itens_para_salvar:
        produto.estoque -= quantidade
        db.add(
            ItemVenda(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=quantidade,
                preco_unitario=produto.preco,
                subtotal=subtotal,
            )
        )

    db.commit()
    db.refresh(venda)
    return venda


@router.get("/minhas", response_model=list[VendaOut])
def minhas_vendas(
    db: Session = Depends(get_db),
    usuario: dict = Depends(usuario_atual),
):
    return (
        db.query(Venda)
        .filter(Venda.usuario_id == usuario["id"])
        .order_by(Venda.criado_em.desc())
        .all()
    )


@router.get("", response_model=list[VendaDetalhada])
def listar_vendas(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    consulta = db.query(Venda)
    if data_inicio:
        consulta = consulta.filter(Venda.criado_em >= datetime.combine(data_inicio, time.min))
    if data_fim:
        consulta = consulta.filter(Venda.criado_em <= datetime.combine(data_fim, time.max))

    vendas = (
        consulta.order_by(Venda.criado_em.desc()).offset(skip).limit(limit).all()
    )
    return [_montar_venda_detalhada(db, venda) for venda in vendas]


@router.get("/{venda_id}", response_model=VendaOut)
def detalhar_venda(
    venda_id: int,
    db: Session = Depends(get_db),
    usuario: dict = Depends(usuario_atual),
):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada."
        )
    if usuario.get("perfil") != "admin" and venda.usuario_id != usuario["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para ver esta venda.",
        )
    return venda


@router.post("/{venda_id}/cancelar", response_model=VendaDetalhada)
def cancelar_venda(
    venda_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada."
        )
    if venda.status == StatusVenda.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta venda já está cancelada."
        )

    for item in venda.itens:
        item.produto.estoque += item.quantidade

    venda.status = StatusVenda.CANCELADA
    db.commit()
    db.refresh(venda)
    return _montar_venda_detalhada(db, venda)
