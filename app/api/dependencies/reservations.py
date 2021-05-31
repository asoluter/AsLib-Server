from datetime import date
from typing import Optional, Dict

from fastapi import Path, Depends, HTTPException, status, Query

from app.api.dependencies.auth import get_current_active_user, verify_user_permissions
from app.api.dependencies.database import get_repository
from app.db.repositories.reservations import ReservationsRepository
from app.models.reservation import ReservationInDB, ReservationStatus
from app.models.user import UserInDB, UserRole


async def get_reservation_by_id_from_path(
    reservation_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    reservation_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> ReservationInDB:
    reservation = await reservation_repo.get_reservation_by_id(id=reservation_id)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reservation found with that id.",
        )
    return reservation


async def verify_reservation_access(
    reservation: ReservationInDB = Depends(get_reservation_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
) -> None:
    if reservation.user_id != current_user.id:
        verify_user_permissions(current_user, UserRole.librarian)


async def get_reservation_filters_from_query(
    book_id: Optional[int] = Query(None, ge=1),
    book_item_id: Optional[int] = Query(None, ge=1),
    library_id: Optional[int] = Query(None, ge=1),
    status: Optional[ReservationStatus] = Query(None),
    due_by: Optional[date] = Query(None),
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict:
    reservation_filters = {}

    if book_id:
        reservation_filters["book_id"] = book_id
    if book_item_id:
        reservation_filters["book_item_id"] = book_item_id
    if library_id:
        reservation_filters["library_id"] = library_id
    if status:
        reservation_filters["status"] = status
    if due_by:
        reservation_filters["due_by"] = due_by

    return reservation_filters
