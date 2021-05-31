from datetime import date
from typing import Optional, Dict

from databases import Database
from fastapi import HTTPException
from starlette import status

from app.db.repositories.base import BaseRepository
from app.db.repositories.book_items import BookItemsRepository
from app.db.repositories.system_config import SystemConfigRepository
from app.db.repositories.users import UsersRepository
from app.models.book_item import BookItemStatus
from app.models.lending import LendingCreate, LendingInDB, ListOfLendingsPublic
from app.models.user import UserStatus

CREATE_LENDING_QUERY = """
    INSERT INTO lendings (user_id, book_item_id, reservation_id, due_date)
    VALUES (:user_id, :book_item_id, :reservation_id, current_date + (SELECT lending_due_day from system_config) * INTERVAL '1 day')
    RETURNING id, user_id, book_item_id, reservation_id, due_date, return_date, fee, created_at, updated_at;
"""

GET_LENDING_BY_ID_QUERY = """
    SELECT id, user_id, book_item_id, reservation_id, due_date, return_date, fee, created_at, updated_at
    FROM lendings
    WHERE id = :id;
"""

LIST_LENDINGS_QUERY_START = """
    SELECT 
        LE.id,
        LE.user_id,
        LE.book_item_id,
        LE.reservation_id,
        LE.due_date,
        LE.return_date,
        LE.fee,
        LE.created_at,
        LE.updated_at,
        count(*) OVER() AS query_count
    FROM lendings LE
"""

UPDATE_LENDING_BY_ID_QUERY = """
    UPDATE lendings
    SET return_date = :return_date,
        fee = :fee
    WHERE id = :id
    RETURNING id, user_id, book_item_id, reservation_id, due_date, return_date, fee, created_at, updated_at;
"""


async def list_lendings_filtered_query(lending_filters: Dict, add_semicolon=True):
    where_query_parts = []

    query = LIST_LENDINGS_QUERY_START

    if lending_filters.get("user_id"):
        where_query_parts.append("LE.user_id = :user_id")
    if lending_filters.get("book_item_id"):
        where_query_parts.append("LE.book_item_id = :book_item_id")
    if lending_filters.get("reservation_id"):
        where_query_parts.append("LE.reservation_id = :reservation_id")
    if lending_filters.get("due_by"):
        where_query_parts.append("LE.due_date < :due_by")
    if returned := lending_filters.get("returned"):
        where_query_parts.append(f"LE.return_date IS {'' if returned else 'NOT'} NULL")

    if where_query_parts:
        query += " WHERE "
        query += " AND ".join(where_query_parts)

    query += " ORDER BY LE.id "

    if lending_filters.get("limit") is not None:
        query += " LIMIT :limit "
    if lending_filters.get("offset") is not None:
        query += " OFFSET :offset "

    if add_semicolon:
        query += ";"

    return query


class LendingsRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.system_config_repo = SystemConfigRepository(db)
        self.users_repo = UsersRepository(db)
        self.book_items_repo = BookItemsRepository(db)

    async def create_lending(self, *, new_lending: LendingCreate, reservation_id: Optional[int] = None) -> LendingInDB:
        async with self.db.transaction():
            user = await self.users_repo.get_user_by_id(id=new_lending.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user found with that id.",
                )
            if user.status != UserStatus.active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Given user is not active.",
                )

            book_item = await self.book_items_repo.get_book_item_by_id(id=new_lending.book_item_id)
            if not book_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user found with that id.",
                )
            if book_item.status != BookItemStatus.available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Given book item is unavailable.",
                )

            created_lending_record = await self.db.fetch_one(
                query=CREATE_LENDING_QUERY, values={**new_lending.dict(), "reservation_id": reservation_id}
            )
            return await self.populate_fee(lending=LendingInDB(**created_lending_record))

    async def get_lending_by_id(self, *, id: int) -> LendingInDB:
        async with self.db.transaction():
            lending_record = await self.db.fetch_one(query=GET_LENDING_BY_ID_QUERY, values={"id": id})
            if lending_record:
                return await self.populate_fee(lending=LendingInDB(**lending_record))

    async def list_lendings(self, *, lending_filters: Dict, limit: int = 20, offset: int = 0) -> ListOfLendingsPublic:
        if lending_filters is None:
            lending_filters = {}

        lending_filters["limit"] = limit
        lending_filters["offset"] = offset

        list_lendings_query = await list_lendings_filtered_query(lending_filters=lending_filters, add_semicolon=False)

        lending_records = await self.db.fetch_all(
            query=list_lendings_query,
            values=lending_filters,
        )

        return ListOfLendingsPublic(
            lendings=[
                await self.populate_fee(lending=LendingInDB(**lending_record)) for lending_record in lending_records
            ],
            lendings_count=lending_records[0].get("query_count") if lending_records else 0,
        )

    async def complete_lending(self, *, lending: LendingInDB) -> LendingInDB:
        async with self.db.transaction():
            if lending.return_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Lending is already completed.",
                )
            lending_with_fee = await self.populate_fee(lending=lending)
            lending_record = await self.db.fetch_one(
                query=UPDATE_LENDING_BY_ID_QUERY,
                values={"id": lending.id, "return_date": date.today(), "fee": lending_with_fee.fee},
            )
            return LendingInDB(**lending_record)

    async def populate_fee(self, *, lending: LendingInDB) -> LendingInDB:
        if lending.fee is not None:
            return lending

        diff = date.today() - lending.due_date
        if diff.days > 0:
            lending.fee = diff.days * (await self.system_config_repo.get_config()).lending_daily_fee

        return lending
