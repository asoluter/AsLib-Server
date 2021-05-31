from fastapi import Path, Depends, HTTPException, status, Query

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.models.user import UserInDB, UserStatus


async def get_user_by_username_from_path(
    username: str = Path(..., min_length=3, regex="^[a-zA-Z0-9_-]+$"),
    current_user: UserInDB = Depends(get_current_active_user),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserInDB:
    user = await users_repo.get_user_by_username(username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that username.",
        )
    return user


async def get_user_by_id_from_query(
    user_id: int = Query(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserInDB:
    user = await users_repo.get_user_by_id(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that id.",
        )
    if not user.status == UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Given user is not active.",
        )
    return user
