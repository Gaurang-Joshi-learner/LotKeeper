from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.models import User
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, auth: AuthService = Depends(get_auth_service)):
    """Create an account (always role `user`) and sign in immediately."""
    user = auth.register(body.email, body.password)
    return TokenOut(access_token=auth.issue_token(user), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, auth: AuthService = Depends(get_auth_service)):
    user = auth.authenticate(body.email, body.password)
    return TokenOut(access_token=auth.issue_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
