from datetime import date
from typing import Dict, Optional

from fastapi import Path, Depends, HTTPException, Query
from starlette import status

from app.api.dependencies.auth import get_current_active_user, verify_user_permissions
from app.api.dependencies.database import get_repository
from app.db.repositories.lendings import LendingsRepository
from app.models.lending import LendingInDB
from app.models.user import UserInDB, UserRole


async def get_lending_by_id_from_path(
    lending_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    lendings_repo: LendingsRepository = Depends(get_repository(LendingsRepository)),
) -> LendingInDB:
    lending = await lendings_repo.get_lending_by_id(id=lending_id)
    if not lending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No lending found with that id.",
        )
    return lending


async def verify_lending_access(
    lending: LendingInDB = Depends(get_lending_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
) -> None:
    if lending.user_id != current_user.id:
        verify_user_permissions(current_user, UserRole.librarian)


async def get_lending_filters_from_query(
    book_item_id: Optional[int] = Query(None, ge=1),
    reservation_id: Optional[int] = Query(None, ge=1),
    due_by: Optional[date] = Query(None),
    returned: Optional[bool] = Query(None),
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict:
    lending_filters = {}

    if book_item_id:
        lending_filters["book_item_id"] = book_item_id
    if reservation_id:
        lending_filters["reservation_id"] = reservation_id
    if due_by:
        lending_filters["due_by"] = due_by
    if returned:
        lending_filters["returned"] = returned

    return lending_filters
