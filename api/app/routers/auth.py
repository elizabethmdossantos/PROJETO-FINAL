from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import criar_token_acesso, verificar_senha
from app.core.config import settings
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.usuario import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.login == dados.login).first()

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Login ou senha incorretos.",
    )

    if not usuario or not usuario.ativo:
        raise credenciais_invalidas

    if not verificar_senha(dados.senha, usuario.senha_hash):
        raise credenciais_invalidas

    if dados.perfil_solicitado == PerfilUsuario.ADMIN:
        if usuario.perfil != PerfilUsuario.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este usuário não possui perfil de administrador.",
            )
        if not settings.ADMIN_MASTER_KEY or dados.senha_admin != settings.ADMIN_MASTER_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Senha administrativa incorreta.",
            )

    token = criar_token_acesso(
        {"sub": usuario.login, "perfil": usuario.perfil.value, "id": usuario.id}
    )

    return TokenResponse(access_token=token, usuario=usuario)
