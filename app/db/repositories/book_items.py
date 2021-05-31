from typing import Dict

from databases import Database
from fastapi import HTTPException, status

from app.db.repositories.base import BaseRepository
from app.db.repositories.libraries import LibrariesRepository
from app.db.repositories.racks import RacksRepository
from app.models.book import BookInDB
from app.models.book_item import (
    BookItemCreate,
    BookItemInDB,
    ListOfBookItemsPublic,
    BookItemInternalUpdate,
    BookItemBase,
)

CREATE_BOOK_ITEM_QUERY = """
    INSERT INTO book_items (barcode, condition, status, book_id, library_id, rack_id)
    VALUES (:barcode, :condition, :status, :book_id, :library_id, :rack_id)
    RETURNING id, barcode, condition, status, book_id, library_id, rack_id, created_at, updated_at;
"""

GET_BOOK_ITEM_BY_ID_QUERY = """
    SELECT id, barcode, condition, status, book_id, library_id, rack_id, created_at, updated_at
    FROM book_items
    WHERE id = :id;
"""

GET_BOOK_ITEM_BY_BARCODE_QUERY = """
    SELECT id, barcode, condition, status, book_id, library_id, rack_id, created_at, updated_at
    FROM book_items
    WHERE barcode = :barcode;
"""

LIST_BOOK_ITEMS_QUERY_START = """
    SELECT 
        id, 
        barcode, 
        condition,
        status, 
        book_id, 
        library_id, 
        rack_id, 
        created_at,
        updated_at,
        count(*) OVER() AS query_count
    FROM book_items BI
"""

UPDATE_BOOK_ITEM_BY_ID_QUERY = """
    UPDATE book_items
    SET barcode = :barcode,
        condition = :condition,
        status = :status,
        library_id = :library_id,
        rack_id = :rack_id
    WHERE id = :id
    RETURNING id, barcode, condition, status, book_id, library_id, rack_id, created_at, updated_at;
"""

DELETE_BOOK_ITEM_BY_ID_QUERY = """
    DELETE FROM book_items
    WHERE id = :id;
"""


async def list_book_items_filtered_query(book_items_filters: Dict, add_semicolon=True):
    where_query_parts = []

    query = LIST_BOOK_ITEMS_QUERY_START

    if book_items_filters.get("condition"):
        where_query_parts.append("BI.condition = :condition")
    if book_items_filters.get("status"):
        where_query_parts.append("BI.status = :status")
    if book_items_filters.get("rack_id"):
        where_query_parts.append("BI.rack_id = :rack_id")
    if book_items_filters.get("library_id"):
        where_query_parts.append("BI.library_id = :library_id")
    if book_items_filters.get("book_id"):
        where_query_parts.append("BI.book_id = :book_id")

    if where_query_parts:
        query += " WHERE "
        query += " AND ".join(where_query_parts)

    query += " ORDER BY BI.id "

    if book_items_filters.get("limit") is not None:
        query += " LIMIT :limit "
    if book_items_filters.get("offset") is not None:
        query += " OFFSET :offset "

    if add_semicolon:
        query += ";"

    return query


class BookItemsRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.libraries_repo = LibrariesRepository(db)
        self.racks_repo = RacksRepository(db)

    async def validate_foreign_keys_update(self, *, book_item: BookItemBase, book_item_update: BookItemBase):
        if book_item_update.barcode and book_item_update.barcode != book_item.barcode:
            if await self.db.fetch_one(
                query=GET_BOOK_ITEM_BY_BARCODE_QUERY, values={"barcode": book_item_update.barcode}
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Given barcode already exists in database.",
                )
        if book_item_update.library_id and book_item_update.library_id != book_item.library_id:
            library = await self.libraries_repo.get_library_by_id(id=book_item_update.library_id)
            if not library:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No library found with that id.",
                )

        if book_item_update.rack_id:
            rack = await self.racks_repo.get_rack_by_id(id=book_item_update.rack_id)
            if not rack:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No rack found with that id.",
                )
            if book_item_update.library_id:
                if rack.library_id != book_item_update.library_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Given rack does not belong to book item library.",
                    )

    async def create_book_item(self, *, book: BookInDB, new_book_item: BookItemCreate) -> BookItemInDB:
        async with self.db.transaction():
            await self.validate_foreign_keys_update(book_item=BookItemBase(), book_item_update=new_book_item)
            created_book_item_record = await self.db.fetch_one(
                query=CREATE_BOOK_ITEM_QUERY, values={**new_book_item.dict(), "book_id": book.id}
            )
            return BookItemInDB(**created_book_item_record)

    async def list_book_items(
        self, *, book_items_filters: Dict, limit: int = 20, offset: int = 0
    ) -> ListOfBookItemsPublic:
        if book_items_filters is None:
            book_items_filters = {}

        book_items_filters["limit"] = limit
        book_items_filters["offset"] = offset

        list_books_query = await list_book_items_filtered_query(book_items_filters=book_items_filters)

        book_item_records = await self.db.fetch_all(
            query=list_books_query,
            values=book_items_filters,
        )

        return ListOfBookItemsPublic(
            book_items=[BookItemInDB(**book_item_record) for book_item_record in book_item_records],
            book_items_count=book_item_records[0].get("query_count") if book_item_records else 0,
        )

    async def get_book_item_by_id(self, *, id: int) -> BookItemInDB:
        book_item_record = await self.db.fetch_one(query=GET_BOOK_ITEM_BY_ID_QUERY, values={"id": id})
        if book_item_record:
            return BookItemInDB(**book_item_record)

    async def get_book_item_by_barcode(self, *, barcode: str) -> BookItemInDB:
        book_item_record = await self.db.fetch_one(query=GET_BOOK_ITEM_BY_BARCODE_QUERY, values={"barcode": barcode})
        if book_item_record:
            return BookItemInDB(**book_item_record)

    async def update_book_item(self, *, book_item: BookItemInDB, book_item_update: BookItemInternalUpdate):
        async with self.db.transaction():
            update_params = book_item.copy(update=book_item_update.dict(exclude_unset=True, exclude_none=True))

            await self.validate_foreign_keys_update(book_item=book_item, book_item_update=book_item_update)

            updated_book_item_record = await self.db.fetch_one(
                query=UPDATE_BOOK_ITEM_BY_ID_QUERY,
                values=update_params.dict(exclude={"created_at", "updated_at", "book_id"}),
            )
            return BookItemInDB(**updated_book_item_record)

    async def delete_book_item(self, *, book_item: BookItemInDB):
        await self.db.execute(query=DELETE_BOOK_ITEM_BY_ID_QUERY, values={"id": book_item.id})
