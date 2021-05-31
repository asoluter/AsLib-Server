from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.models.token import AccessToken
from app.services import jwt

router = APIRouter()


@router.post("/login", response_model=AccessToken, name="auth:login-existing-user")
async def user_login(
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
) -> AccessToken:
    user = await user_repo.authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authentication was unsuccessful.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = AccessToken(access_token=jwt.create_access_token_for_user(user=user), token_type="bearer")
    return access_token
