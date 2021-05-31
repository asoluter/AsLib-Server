from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import SECRET_KEY, API_PREFIX
from app.models.user import UserInDB, UserRole, UserStatus
from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.services import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/auth/login")


async def get_user_from_token(
    *,
    token: str = Depends(oauth2_scheme),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> Optional[UserInDB]:
    try:
        username = jwt.get_username_from_token(token=token, secret_key=str(SECRET_KEY))
        user = await user_repo.get_user_by_username(username=username)
    except Exception as e:
        raise e
    return user


def get_current_active_user(current_user: UserInDB = Depends(get_user_from_token)) -> Optional[UserInDB]:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authenticated user.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.status == UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not an active user.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def verify_user_permissions(user: UserInDB, role: UserRole) -> None:
    if UserRole.get_numeric_value(user.role) < UserRole.get_numeric_value(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You're not authorized to access this resource",
        )


def get_current_active_user_with_permissions(role: UserRole) -> Callable:
    def get_user(
        current_user: UserInDB = Depends(get_current_active_user),
    ) -> Optional[UserInDB]:
        verify_user_permissions(current_user, role)
        return current_user

    return get_user
