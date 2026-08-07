from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import usuario_atual, exigir_admin
from app.models.produto import Produto
from app.schemas.produto import ProdutoCriar, ProdutoAtualizar, ProdutoOut

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoCriar,
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    if db.query(Produto).filter(Produto.codigo == dados.codigo).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um produto com esse código.",
        )
    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("", response_model=list[ProdutoOut])
def listar_produtos(
    apenas_ativos: bool = True,
    busca: str = "",
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    consulta = db.query(Produto)
    if apenas_ativos:
        consulta = consulta.filter(Produto.ativo.is_(True))
    if busca:
        consulta = consulta.filter(
            (Produto.nome.ilike(f"%{busca}%")) | (Produto.codigo.ilike(f"%{busca}%"))
        )
    return consulta.order_by(Produto.nome).offset(skip).limit(limit).all()


@router.get("/codigo/{codigo}", response_model=ProdutoOut)
def buscar_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    _usuario: dict = Depends(usuario_atual),
):
    produto = (
        db.query(Produto)
        .filter(Produto.codigo == codigo, Produto.ativo.is_(True))
        .first()
    )
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado ou inativo.",
        )
    return produto


@router.get("/{produto_id}", response_model=ProdutoOut)
def buscar_por_id(
    produto_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado."
        )
    return produto


@router.patch("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: int,
    dados: ProdutoAtualizar,
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado."
        )
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    return produto
