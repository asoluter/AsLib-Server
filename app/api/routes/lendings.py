from typing import Dict, Optional

from fastapi import Depends, Body, Query, APIRouter
from starlette.status import HTTP_201_CREATED

from app.api.dependencies.auth import get_current_active_user_with_permissions, get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.lendings import (
    get_lending_by_id_from_path,
    verify_lending_access,
    get_lending_filters_from_query,
)
from app.core.config import PAGE_LIMIT
from app.db.repositories.lendings import LendingsRepository
from app.models.lending import LendingPublic, LendingInDB, ListOfLendingsPublic, LendingCreate
from app.models.user import UserInDB, UserRole

router = APIRouter()


@router.post("/", response_model=LendingPublic, name="lendings:create-lending", status_code=HTTP_201_CREATED)
async def create_new_lending(
    new_lending: LendingCreate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    lendings_repo: LendingsRepository = Depends(get_repository(LendingsRepository)),
) -> LendingPublic:
    return await lendings_repo.create_lending(new_lending=new_lending)


@router.get("/", response_model=ListOfLendingsPublic, name="lendings:list-lendings")
async def list_lendings(
    page: int = Query(1, ge=1),
    user_id: Optional[int] = Query(None, ge=1),
    lending_filters: Dict = Depends(get_lending_filters_from_query),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    lendings_repo: LendingsRepository = Depends(get_repository(LendingsRepository)),
) -> ListOfLendingsPublic:
    if user_id:
        lending_filters["user_id"] = user_id
    return await lendings_repo.list_lendings(
        lending_filters=lending_filters,
        limit=PAGE_LIMIT,
        offset=(page - 1) * PAGE_LIMIT,
    )


@router.get("/my/", response_model=ListOfLendingsPublic, name="lendings:list-current-user-lendings")
async def list_lendings_for_current_user(
    page: int = Query(1, ge=1),
    lending_filters: Dict = Depends(get_lending_filters_from_query),
    current_user: UserInDB = Depends(get_current_active_user),
    lendings_repo: LendingsRepository = Depends(get_repository(LendingsRepository)),
) -> ListOfLendingsPublic:
    lending_filters["user_id"] = current_user.id
    return await lendings_repo.list_lendings(
        lending_filters=lending_filters,
        limit=PAGE_LIMIT,
        offset=(page - 1) * PAGE_LIMIT,
    )


@router.get(
    "/{lending_id}/",
    response_model=LendingPublic,
    name="lendings:get-lending-by-id",
    dependencies=[Depends(verify_lending_access)],
)
async def get_lending_by_id(
    lending: LendingInDB = Depends(get_lending_by_id_from_path),
) -> LendingPublic:
    return lending


@router.put("/{lending_id}/complete", response_model=LendingPublic, name="lendings:complete-lending-by-id")
async def complete_lending(
    lending: LendingInDB = Depends(get_lending_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    lendings_repo: LendingsRepository = Depends(get_repository(LendingsRepository)),
) -> LendingPublic:
    return await lendings_repo.complete_lending(lending=lending)
