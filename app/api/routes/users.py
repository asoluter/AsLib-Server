from fastapi import APIRouter, Depends, Body, HTTPException, status, Query
from starlette.status import HTTP_201_CREATED

from app.api.dependencies.auth import (
    get_current_active_user,
    verify_user_permissions,
    get_current_active_user_with_permissions,
)
from app.api.dependencies.database import get_repository
from app.api.dependencies.users import get_user_by_username_from_path
from app.core.config import PAGE_LIMIT
from app.db.repositories.users import UsersRepository
from app.models.user import (
    UserPublic,
    UserInDB,
    UserRole,
    CurrentUserUpdate,
    UserUpdate,
    UserCreate,
    UserStatus,
    ListOfUsersPublic,
)

router = APIRouter()


@router.post("/", response_model=UserPublic, name="users:register-new-user", status_code=HTTP_201_CREATED)
async def register_new_user(
    new_user: UserCreate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    if (
        UserRole.get_numeric_value(new_user.role) > UserRole.get_numeric_value(UserRole.default)
        or new_user.status != UserStatus.active
    ):
        if UserRole.get_numeric_value(current_user.role) < UserRole.get_numeric_value(UserRole.admin):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Administrators are allowed to change user roles and statuses",
            )
    created_user = await user_repo.register_new_user(new_user=new_user)
    return created_user


@router.get("/", response_model=ListOfUsersPublic, name="users:list-users")
async def list_users(
    page: int = Query(1, ge=1),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> ListOfUsersPublic:
    return ListOfUsersPublic(
        users=await user_repo.list_users(limit=PAGE_LIMIT, offset=(page - 1) * PAGE_LIMIT),
        users_count=await user_repo.users_count(),
    )


@router.get("/me/", response_model=UserPublic, name="users:get-current-user")
async def get_currently_authenticated_user(current_user: UserInDB = Depends(get_current_active_user)) -> UserPublic:
    return current_user


@router.get("/{username}/", response_model=UserPublic, name="users:get-user")
async def get_user_by_username(
    user: UserInDB = Depends(get_user_by_username_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserPublic:
    if user.id != current_user.id:
        verify_user_permissions(current_user, UserRole.librarian)
    return user


@router.put("/me/", response_model=UserPublic, name="users:update-current-user")
async def update_current_user(
    user_update: CurrentUserUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    updated_user = await user_repo.update_user(user=current_user, user_update=user_update)
    return updated_user


@router.put("/{username}/", response_model=UserPublic, name="users:update-user")
async def update_user_by_username(
    user_update: UserUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    user: UserInDB = Depends(get_user_by_username_from_path),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    update_params = user_update.dict(exclude_unset=True)

    if any(key in update_params for key in ("role", "status")):
        if UserRole.get_numeric_value(current_user.role) < UserRole.get_numeric_value(UserRole.admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Administrators are allowed to change user roles and statuses",
            )

    updated_user = await user_repo.update_user(user=user, user_update=user_update)
    return updated_user
