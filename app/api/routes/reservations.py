from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends, Query
from starlette.status import HTTP_201_CREATED

from app.api.dependencies.auth import get_current_active_user_with_permissions, get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.reservations import (
    verify_reservation_access,
    get_reservation_by_id_from_path,
    get_reservation_filters_from_query,
)
from app.core.config import PAGE_LIMIT
from app.db.repositories.reservations import ReservationsRepository
from app.models.lending import LendingPublic
from app.models.reservation import (
    ReservationPublic,
    ReservationCreate,
    ReservationCreateMy,
    ListOfReservationsPublic,
    ReservationInDB,
)
from app.models.user import UserRole, UserInDB

router = APIRouter()


@router.post(
    "/", response_model=ReservationPublic, name="reservations:create-reservation", status_code=HTTP_201_CREATED
)
async def create_new_reservation(
    new_reservation: ReservationCreate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    reservations_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> ReservationPublic:
    return await reservations_repo.create_reservation(new_reservation=new_reservation, requesting_user=current_user)


@router.post(
    "/my/",
    response_model=ReservationPublic,
    name="reservations:create-reservation-for-current-user",
    status_code=HTTP_201_CREATED,
)
async def create_new_reservation_for_current_user(
    new_reservation: ReservationCreateMy = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user),
    reservations_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> ReservationPublic:
    return await reservations_repo.create_reservation(
        new_reservation=ReservationCreate(**new_reservation.dict(), user_id=current_user.id),
        requesting_user=current_user,
    )


@router.get("/", response_model=ListOfReservationsPublic, name="reservations:list-reservations")
async def list_reservations(
    page: int = Query(1, ge=1),
    user_id: Optional[int] = Query(None, ge=1),
    reservation_filters: Dict = Depends(get_reservation_filters_from_query),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    reservations_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> ListOfReservationsPublic:
    if user_id:
        reservation_filters["user_id"] = user_id
    return await reservations_repo.list_reservations(
        reservation_filters=reservation_filters,
        limit=PAGE_LIMIT,
        offset=(page - 1) * PAGE_LIMIT,
    )


@router.get("/my/", response_model=ListOfReservationsPublic, name="reservations:list-current-user-reservations")
async def list_reservations_for_current_user(
    page: int = Query(1, ge=1),
    reservation_filters: Dict = Depends(get_reservation_filters_from_query),
    current_user: UserInDB = Depends(get_current_active_user),
    reservations_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> ListOfReservationsPublic:
    reservation_filters["user_id"] = current_user.id
    return await reservations_repo.list_reservations(
        reservation_filters=reservation_filters,
        limit=PAGE_LIMIT,
        offset=(page - 1) * PAGE_LIMIT,
    )


@router.get(
    "/{reservation_id}/",
    response_model=ReservationPublic,
    name="reservations:get-reservation-by-id",
    dependencies=[Depends(verify_reservation_access)],
)
async def get_reservation_by_id(
    reservation: ReservationInDB = Depends(get_reservation_by_id_from_path),
) -> ReservationPublic:
    return reservation


@router.put(
    "/{reservation_id}/fulfill", response_model=ReservationPublic, name="reservations:fulfill-reservation-by-id"
)
async def accept_reservation(
    book_item_id: int = Query(..., ge=1),
    reservation: ReservationInDB = Depends(get_reservation_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    reservations_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> ReservationPublic:
    return await reservations_repo.fulfill_reservation(reservation=reservation, book_item_id=book_item_id)


@router.put(
    "/{reservation_id}/cancel",
    response_model=ReservationPublic,
    name="reservations:cancel-reservation-by-id",
    dependencies=[Depends(verify_reservation_access)],
)
async def cancel_reservation(
    reservation: ReservationInDB = Depends(get_reservation_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
    reservations_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> ReservationPublic:
    return await reservations_repo.cancel_reservation(reservation=reservation)


@router.put("/{reservation_id}/complete", response_model=LendingPublic, name="reservations:complete-reservation-by-id")
async def complete_reservation(
    reservation: ReservationInDB = Depends(get_reservation_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    reservations_repo: ReservationsRepository = Depends(get_repository(ReservationsRepository)),
) -> LendingPublic:
    return await reservations_repo.complete_reservation(reservation=reservation)
