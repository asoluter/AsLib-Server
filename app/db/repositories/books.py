from typing import List, Dict

from databases import Database
from fastapi import HTTPException
from starlette import status

from app.db.repositories.authors import AuthorsRepository
from app.db.repositories.base import BaseRepository
from app.models.book import BookCreate, BookPublic, BookInDB, BookUpdate, ListOfBooksPublic

CREATE_BOOK_QUERY = """
    INSERT INTO books (isbn, title, description, publisher, page_count, publish_date)
    VALUES (:isbn, :title, :description, :publisher, :page_count, :publish_date)
    RETURNING id, isbn, title, description, publisher, page_count, publish_date, created_at, updated_at;
"""

GET_BOOK_BY_ID_QUERY = """
    SELECT id, isbn, title, description, publisher, page_count, publish_date, created_at, updated_at
    FROM books
    WHERE id = :id;
"""

GET_BOOK_BY_ISBN_QUERY = """
    SELECT id, isbn, title, description, publisher, page_count, publish_date, created_at, updated_at
    FROM books
    WHERE isbn = :isbn;
"""

LIST_BOOKS_QUERY_START = """
    SELECT 
        B.id,
        B.isbn,
        B.title,
        B.description,
        B.publisher,
        B.page_count,
        B.publish_date,
        B.created_at,
        B.updated_at,
        count(*) OVER() AS query_count
    FROM books B
"""

UPDATE_BOOK_BY_ID_QUERY = """
    UPDATE books
    SET isbn = :isbn,
        title = :title,
        description = :description,
        publisher = :publisher,
        page_count = :page_count,
        publish_date = :publish_date
    WHERE id = :id
    RETURNING id, isbn, title, description, publisher, page_count, publish_date, created_at, updated_at;
"""

DELETE_BOOK_BY_ID_QUERY = """
    DELETE FROM books
    WHERE id = :id;
"""

GET_BOOK_AUTHORS_BY_ID_QUERY = """
    SELECT author_name
    FROM books_to_authors
    WHERE book_id = :book_id;
"""

ADD_BOOK_AUTHOR_QUERY = """
    INSERT INTO books_to_authors (book_id, author_name)
    VALUES (:book_id, :author_name)
    ON CONFLICT DO NOTHING;
"""

REMOVE_BOOK_AUTHOR_QUERY = """
    DELETE FROM books_to_authors
    WHERE book_id = :book_id
        AND author_name = :author_name;
"""


async def list_books_filtered_query(book_filters: Dict, add_semicolon=True):
    where_query_parts = []
    join_query_parts = []
    query = LIST_BOOKS_QUERY_START

    if book_filters.get("inisbn"):
        where_query_parts.append("B.isbn ILIKE :inisbn")
    if book_filters.get("inauthor"):
        where_query_parts.append("BA.author_name ILIKE :inauthor")
        join_query_parts.append("INNER JOIN books_to_authors BA ON B.id = BA.book_id")
    if book_filters.get("intitle"):
        where_query_parts.append("B.title ILIKE :intitle")
    if book_filters.get("inpublisher"):
        where_query_parts.append("B.publisher ILIKE :inpublisher")
    if book_filters.get("publish_date"):
        where_query_parts.append("publish_date = :publish_date")

    join_book_items = False
    if book_filters.get("library_id"):
        where_query_parts.append("BI.library_id = :library_id")
        join_book_items = True
    if book_filters.get("rack_id"):
        where_query_parts.append("BI.rack_id = :rack_id")
        join_book_items = True

    if join_book_items:
        join_query_parts.append("INNER JOIN book_items BI ON BI.book_id = B.id")

    if join_query_parts:
        query += f" {' '.join(join_query_parts)} "

    if where_query_parts:
        query += " WHERE "
        query += " AND ".join(where_query_parts)

    query += " GROUP BY B.id "
    query += " ORDER BY B.id "

    if book_filters.get("limit") is not None:
        query += " LIMIT :limit "
    if book_filters.get("offset") is not None:
        query += " OFFSET :offset "

    if add_semicolon:
        query += ";"

    return query


class BooksRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.authors_repo = AuthorsRepository(db)

    async def check_isbn_exists(self, isbn: str):
        if await self.get_book_by_isbn(isbn=isbn, populate=False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Given isbn already exists in database.",
            )

    async def create_book(self, *, new_book: BookCreate, populate: bool = True) -> BookPublic:
        async with self.db.transaction():
            await self.check_isbn_exists(new_book.isbn)
            created_book_record = await self.db.fetch_one(
                query=CREATE_BOOK_QUERY, values=new_book.dict(exclude={"authors"})
            )
            created_book = BookInDB(**created_book_record)
            if new_book.authors:
                await self.authors_repo.create_authors_that_dont_exist(authors=new_book.authors)
                await self.db.execute_many(
                    query=ADD_BOOK_AUTHOR_QUERY,
                    values=[{"book_id": created_book.id, "author_name": name} for name in new_book.authors],
                )
            if populate:
                return await self.populate_book(book=created_book)
            return created_book

    async def get_book_by_id(self, *, id: int, populate: bool = True) -> BookInDB:
        book_record = await self.db.fetch_one(query=GET_BOOK_BY_ID_QUERY, values={"id": id})
        if book_record:
            book = BookInDB(**book_record)
            if populate:
                return await self.populate_book(book=book)
            return book

    async def get_book_by_isbn(self, *, isbn: str, populate: bool = True) -> BookInDB:
        book_record = await self.db.fetch_one(query=GET_BOOK_BY_ISBN_QUERY, values={"isbn": isbn})
        if book_record:
            book = BookInDB(**book_record)
            if populate:
                return await self.populate_book(book=book)
            return book

    async def list_books(
        self,
        *,
        book_filters: Dict = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ListOfBooksPublic:
        if book_filters is None:
            book_filters = {}

        book_filters["limit"] = limit
        book_filters["offset"] = offset

        list_books_query = await list_books_filtered_query(book_filters=book_filters, add_semicolon=False)

        book_records = await self.db.fetch_all(
            query=list_books_query,
            values=book_filters,
        )

        return ListOfBooksPublic(
            books=[await self.populate_book(book=BookInDB(**book_record)) for book_record in book_records],
            books_count=book_records[0].get("query_count") if book_records else 0,
        )

    async def update_book(self, *, book: BookInDB, book_update: BookUpdate, populate: bool = True) -> BookInDB:
        async with self.db.transaction():
            if not book_update.title:
                book_update.title = book.title
            update_params = book.copy(update=book_update.dict(exclude_unset=True, exclude={"authors"}))
            await self.check_isbn_exists(book_update.isbn)
            updated_book_record = await self.db.fetch_one(
                query=UPDATE_BOOK_BY_ID_QUERY,
                values=update_params.dict(exclude={"created_at", "updated_at"}),
            )
            updated_book = BookInDB(**updated_book_record)
            if book_update.authors:
                current_book_authors = await self.get_book_authors(book=updated_book)
                removed_book_authors = [name for name in current_book_authors if name not in book_update.authors]
                await self.authors_repo.create_authors_that_dont_exist(authors=book_update.authors)
                if removed_book_authors:
                    await self.db.execute_many(
                        query=REMOVE_BOOK_AUTHOR_QUERY,
                        values=[{"book_id": updated_book.id, "author_name": name} for name in removed_book_authors],
                    )
                await self.db.execute_many(
                    query=ADD_BOOK_AUTHOR_QUERY,
                    values=[{"book_id": updated_book.id, "author_name": name} for name in book_update.authors],
                )

            if populate:
                return await self.populate_book(book=updated_book)
            return updated_book

    async def delete_book(self, *, book: BookInDB):
        await self.db.execute(query=DELETE_BOOK_BY_ID_QUERY, values={"id": book.id})

    async def get_book_authors(self, *, book: BookInDB) -> List[str]:
        author_rows = await self.db.fetch_all(query=GET_BOOK_AUTHORS_BY_ID_QUERY, values={"book_id": book.id})
        return [author.get("author_name") for author in author_rows]

    async def populate_book(self, *, book: BookInDB) -> BookPublic:
        return BookPublic(
            **book.dict(),
            authors=await self.get_book_authors(book=book),
        )
