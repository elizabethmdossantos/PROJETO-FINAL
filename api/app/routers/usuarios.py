from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import exigir_admin
from app.core.security import gerar_hash_senha
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

# Todas as rotas abaixo são restritas ao administrador: é aqui que perfis são
# concedidos, então nunca podem ficar acessíveis sem autenticação.


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    return (
        db.query(Usuario)
        .order_by(Usuario.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    existente = db.query(Usuario).filter(Usuario.login == dados.login).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com este login.",
        )

    usuario = Usuario(
        nome=dados.nome,
        login=dados.login,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil=PerfilUsuario(dados.perfil),
        ativo=dados.ativo,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioOut)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    if dados.login is not None:
        existente = db.query(Usuario).filter(Usuario.login == dados.login, Usuario.id != usuario_id).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário com este login.",
            )
        usuario.login = dados.login

    if dados.nome is not None:
        usuario.nome = dados.nome

    if dados.perfil is not None:
        usuario.perfil = dados.perfil

    if dados.ativo is not None:
        usuario.ativo = dados.ativo

    if dados.senha is not None:
        usuario.senha_hash = gerar_hash_senha(dados.senha)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(exigir_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    if usuario.login == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuário não pode ser removido.",
        )

    db.delete(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não é possível excluir este usuário: existem caixas ou vendas "
                "vinculados a ele. Desative-o em vez de excluir."
            ),
        )
    return None
