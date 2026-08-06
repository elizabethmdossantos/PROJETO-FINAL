from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import usuario_atual, exigir_admin
from app.models.caixa import Caixa, StatusCaixa
from app.models.venda import Venda, StatusVenda, FormaPagamento
from app.schemas.caixa import CaixaAbrir, CaixaFechar, CaixaOut, CaixaResumo

router = APIRouter(prefix="/caixa", tags=["Caixa"])


def _buscar_caixa_aberto(db: Session, usuario_id: int) -> Optional[Caixa]:
    return (
        db.query(Caixa)
        .filter(Caixa.usuario_id == usuario_id, Caixa.status == StatusCaixa.ABERTO)
        .first()
    )


@router.post("/abrir", response_model=CaixaOut, status_code=status.HTTP_201_CREATED)
def abrir_caixa(
    dados: CaixaAbrir,
    db: Session = Depends(get_db),
    usuario: dict = Depends(usuario_atual),
):
    if _buscar_caixa_aberto(db, usuario["id"]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já tem um caixa aberto. Feche-o antes de abrir outro.",
        )

    caixa = Caixa(
        usuario_id=usuario["id"],
        valor_abertura=dados.valor_abertura,
        observacoes=dados.observacoes,
        status=StatusCaixa.ABERTO,
    )
    db.add(caixa)
    db.commit()
    db.refresh(caixa)
    return caixa


@router.get("/atual", response_model=CaixaOut)
def caixa_atual(
    db: Session = Depends(get_db),
    usuario: dict = Depends(usuario_atual),
):
    caixa = _buscar_caixa_aberto(db, usuario["id"])
    if not caixa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você não tem nenhum caixa aberto no momento.",
        )
    return caixa


@router.post("/fechar", response_model=CaixaResumo)
def fechar_caixa(
    dados: CaixaFechar,
    db: Session = Depends(get_db),
    usuario: dict = Depends(usuario_atual),
):
    caixa = _buscar_caixa_aberto(db, usuario["id"])
    if not caixa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você não tem nenhum caixa aberto para fechar.",
        )

    vendas_do_turno = (
        db.query(Venda)
        .filter(Venda.caixa_id == caixa.id, Venda.status == StatusVenda.CONCLUIDA)
        .all()
    )

    def total_por_forma(forma: FormaPagamento) -> Decimal:
        return sum(
            (v.valor_total for v in vendas_do_turno if v.forma_pagamento == forma),
            Decimal("0"),
        )

    total_vendas = sum((v.valor_total for v in vendas_do_turno), Decimal("0"))

    caixa.status = StatusCaixa.FECHADO
    caixa.valor_fechamento = dados.valor_fechamento
    caixa.fechado_em = datetime.utcnow()
    if dados.observacoes:
        caixa.observacoes = dados.observacoes

    db.commit()
    db.refresh(caixa)

    return CaixaResumo(
        **CaixaOut.model_validate(caixa).model_dump(),
        total_vendas=total_vendas,
        quantidade_vendas=len(vendas_do_turno),
        total_pix=total_por_forma(FormaPagamento.PIX),
        total_cartao=total_por_forma(FormaPagamento.CARTAO),
        total_vale_refeicao=total_por_forma(FormaPagamento.VALE_REFEICAO),
    )


@router.get("", response_model=list[CaixaOut])
def listar_caixas(
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    return (
        db.query(Caixa)
        .order_by(Caixa.aberto_em.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
