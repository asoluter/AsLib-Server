import datetime
from typing import Dict

from databases import Database
from fastapi import HTTPException, status

from app.db.repositories.base import BaseRepository
from app.db.repositories.book_items import BookItemsRepository
from app.db.repositories.books import BooksRepository
from app.db.repositories.lendings import LendingsRepository
from app.db.repositories.libraries import LibrariesRepository
from app.db.repositories.users import UsersRepository
from app.models.book_item import BookItemStatus, BookItemInternalUpdate
from app.models.lending import LendingInDB, LendingCreate
from app.models.reservation import ReservationCreate, ReservationInDB, ReservationStatus, ListOfReservationsPublic
from app.models.user import UserInDB, UserStatus

CREATE_RESERVATION_QUERY = """
    INSERT INTO reservations (book_id, library_id, user_id, status)
    VALUES (:book_id, :library_id, :user_id, :status)
    RETURNING id, book_id, library_id, user_id, status, book_item_id, due_date, created_at, updated_at;
"""

GET_RESERVATION_BY_ID_QUERY = """
    SELECT id, book_id, library_id, user_id, status, book_item_id, due_date, created_at, updated_at
    FROM reservations
    WHERE id = :id;
"""

LIST_RESERVATIONS_QUERY_START = """
    SELECT 
        R.id,
        R.book_id,
        R.library_id,
        R.user_id,
        R.status,
        R.book_item_id,
        R.due_date,
        R.created_at,
        R.updated_at,
        count(*) OVER() AS query_count
    FROM reservations R
"""

UPDATE_RESERVATION_BY_ID_QUERY = """
    UPDATE reservations
    SET book_item_id = :book_item_id,
        status = :status,
        due_date = current_date + (SELECT reservation_due_day from system_config) * INTERVAL '1 day'
    WHERE id = :id
    RETURNING id, book_id, library_id, user_id, status, book_item_id, due_date, created_at, updated_at;
"""


async def list_reservations_filtered_query(reservation_filters: Dict, add_semicolon=True):
    where_query_parts = []

    query = LIST_RESERVATIONS_QUERY_START

    if reservation_filters.get("book_id"):
        where_query_parts.append("R.book_id = :book_id")
    if reservation_filters.get("book_item_id"):
        where_query_parts.append("R.book_item_id = :book_item_id")
    if reservation_filters.get("library_id"):
        where_query_parts.append("R.library_id = :library_id")
    if reservation_filters.get("user_id"):
        where_query_parts.append("R.user_id = :user_id")
    if reservation_filters.get("status"):
        where_query_parts.append("R.status = :status")
    if reservation_filters.get("due_by"):
        where_query_parts.append("R.due_date < :due_by")

    if where_query_parts:
        query += " WHERE "
        query += " AND ".join(where_query_parts)

    query += " ORDER BY R.id "

    if reservation_filters.get("limit") is not None:
        query += " LIMIT :limit "
    if reservation_filters.get("offset") is not None:
        query += " OFFSET :offset "

    if add_semicolon:
        query += ";"

    return query


class ReservationsRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)
        self.books_repo = BooksRepository(db)
        self.book_items_repo = BookItemsRepository(db)
        self.libraries_repo = LibrariesRepository(db)
        self.lendings_repo = LendingsRepository(db)

    async def validate_user_and_library(self, reservation, requesting_user: UserInDB):
        if requesting_user.id != reservation.user_id:
            user = await self.users_repo.get_user_by_id(id=reservation.user_id)
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
        if not await self.libraries_repo.get_library_by_id(id=reservation.library_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No library found with that id.",
            )

    async def create_reservation(
        self, *, new_reservation: ReservationCreate, requesting_user: UserInDB
    ) -> ReservationInDB:
        async with self.db.transaction():
            if not new_reservation.user_id:
                new_reservation.user_id = requesting_user.id
            await self.validate_user_and_library(new_reservation, requesting_user)
            if not await self.books_repo.get_book_by_id(id=new_reservation.book_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No book found with that id.",
                )
            created_reservation_record = await self.db.fetch_one(
                query=CREATE_RESERVATION_QUERY, values={**new_reservation.dict(), "status": ReservationStatus.pending}
            )
            return ReservationInDB(**created_reservation_record)

    async def get_reservation_by_id(self, *, id: int) -> ReservationInDB:
        reservation_record = await self.db.fetch_one(query=GET_RESERVATION_BY_ID_QUERY, values={"id": id})
        if reservation_record:
            return ReservationInDB(**reservation_record)

    async def list_reservations(
        self, *, reservation_filters: Dict, limit: int = 20, offset: int = 0
    ) -> ListOfReservationsPublic:
        if reservation_filters is None:
            reservation_filters = {}

        reservation_filters["limit"] = limit
        reservation_filters["offset"] = offset

        list_reservations_query = await list_reservations_filtered_query(
            reservation_filters=reservation_filters, add_semicolon=False
        )

        reservation_records = await self.db.fetch_all(
            query=list_reservations_query,
            values=reservation_filters,
        )

        return ListOfReservationsPublic(
            reservations=[ReservationInDB(**reservation_record) for reservation_record in reservation_records],
            reservations_count=reservation_records[0].get("query_count") if reservation_records else 0,
        )

    async def fulfill_reservation(self, *, reservation: ReservationInDB, book_item_id: int) -> ReservationInDB:
        async with self.db.transaction():
            if reservation.status != ReservationStatus.pending:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Reservation is already {reservation.status}.",
                )
            if reservation.book_item_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reservation is already fulfilled.",
                )
            book_item = await self.book_items_repo.get_book_item_by_id(id=book_item_id)
            if not book_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No book item found with that id.",
                )
            if book_item.status != BookItemStatus.available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Given book item is unavailable.",
                )
            if book_item.library_id != reservation.library_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Given book item does not belong to reservation library.",
                )
            await self.book_items_repo.update_book_item(
                book_item=book_item, book_item_update=BookItemInternalUpdate(status=BookItemStatus.reserved)
            )
            updated_reservation_record = await self.db.fetch_one(
                query=UPDATE_RESERVATION_BY_ID_QUERY,
                values={"id": reservation.id, "book_item_id": book_item_id, "status": ReservationStatus.waiting},
            )
            return ReservationInDB(**updated_reservation_record)

    async def cancel_reservation(self, *, reservation: ReservationInDB) -> ReservationInDB:
        async with self.db.transaction():
            if reservation.status in {ReservationStatus.cancelled, ReservationStatus.completed}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Reservation is already {reservation.status}.",
                )
            book_item = await self.book_items_repo.get_book_item_by_id(id=reservation.book_item_id)
            if book_item and book_item.status not in {BookItemStatus.lost, BookItemStatus.written_off}:
                await self.book_items_repo.update_book_item(
                    book_item=book_item, book_item_update=BookItemInternalUpdate(status=BookItemStatus.available)
                )

            updated_reservation_record = await self.db.fetch_one(
                query=UPDATE_RESERVATION_BY_ID_QUERY,
                values={
                    "id": reservation.id,
                    "book_item_id": reservation.book_item_id,
                    "status": ReservationStatus.cancelled,
                },
            )
            return ReservationInDB(**updated_reservation_record)

    async def complete_reservation(self, *, reservation: ReservationInDB) -> LendingInDB:
        async with self.db.transaction():
            if reservation.status in {ReservationStatus.cancelled, ReservationStatus.completed}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Reservation is already {reservation.status}.",
                )

            book_item = await self.book_items_repo.get_book_item_by_id(id=reservation.book_item_id)
            if not book_item or book_item.status in {BookItemStatus.lost, BookItemStatus.written_off}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reserved book item is unavailable.",
                )
            await self.book_items_repo.update_book_item(
                book_item=book_item, book_item_update=BookItemInternalUpdate(status=BookItemStatus.available)
            )

            updated_reservation_record = await self.db.fetch_one(
                query=UPDATE_RESERVATION_BY_ID_QUERY,
                values={
                    "id": reservation.id,
                    "book_item_id": reservation.book_item_id,
                    "status": ReservationStatus.completed,
                },
            )

            new_lending = LendingCreate(user_id=reservation.user_id, book_item_id=reservation.book_item_id)
            return await self.lendings_repo.create_lending(new_lending=new_lending, reservation_id=reservation.id)

    async def cancel_due_reservations(self):
        due_reservations = await self.list_reservations(
            reservation_filters={"due_by": datetime.date.today(), "status": ReservationStatus.waiting},
            limit=None,
            offset=None,
        )

        for reservation in due_reservations.reservations:
            await self.cancel_reservation(reservation=reservation)
