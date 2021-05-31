from typing import Optional, Dict

from fastapi import APIRouter, Body, Depends, Query
from starlette.status import HTTP_201_CREATED

from app.api.dependencies.auth import get_current_active_user, get_current_active_user_with_permissions
from app.api.dependencies.book_items import get_book_items_filters_from_query
from app.api.dependencies.books import get_book_by_id_from_path, get_book_filters_from_query
from app.core.config import PAGE_LIMIT
from app.db.repositories.book_items import BookItemsRepository
from app.db.repositories.books import BooksRepository
from app.api.dependencies.database import get_repository
from app.models.book import BookPublic, BookCreate, BookInDB, ListOfBooksPublic, BookUpdate
from app.models.book_item import BookItemPublic, BookItemCreate, ListOfBookItemsPublic
from app.models.user import UserInDB, UserRole

router = APIRouter()


@router.post("/", response_model=BookPublic, name="books:create-book", status_code=HTTP_201_CREATED)
async def create_new_book(
    new_book: BookCreate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> BookPublic:
    return await books_repo.create_book(new_book=new_book)


@router.get("/", response_model=ListOfBooksPublic, name="books:list-books")
async def list_books(
    page: int = Query(1, ge=1),
    book_filters: Dict = Depends(get_book_filters_from_query),
    current_user: UserInDB = Depends(get_current_active_user),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> ListOfBooksPublic:
    return await books_repo.list_books(
        book_filters=book_filters,
        limit=PAGE_LIMIT,
        offset=(page - 1) * PAGE_LIMIT,
    )


@router.get("/{book_id}/", response_model=BookPublic, name="books:get-book-by-id")
async def get_book_by_id(
    book: BookInDB = Depends(get_book_by_id_from_path),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> BookPublic:
    return await books_repo.populate_book(book=book)


@router.put(
    "/{book_id}/",
    response_model=BookPublic,
    name="books:update-book-by-id",
)
async def update_book_by_id(
    book: BookInDB = Depends(get_book_by_id_from_path),
    book_update: BookUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> BookPublic:
    return await books_repo.update_book(book=book, book_update=book_update)


@router.delete(
    "/{book_id}/",
    name="books:delete-book-by-id",
)
async def delete_book_by_id(
    book: BookInDB = Depends(get_book_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> None:
    await books_repo.delete_book(book=book)


@router.post(
    "/{book_id}/items", response_model=BookItemPublic, name="books:create-book-item", status_code=HTTP_201_CREATED
)
async def create_new_book(
    new_book_item: BookItemCreate = Body(..., embed=True),
    book: BookInDB = Depends(get_book_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    books_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> BookItemPublic:
    return await books_items_repo.create_book_item(book=book, new_book_item=new_book_item)


@router.get("/{book_id}/items", response_model=ListOfBookItemsPublic, name="books:get-book-items")
async def get_book_items(
    page: int = Query(1, ge=1),
    library_id: Optional[int] = Query(None, ge=1),
    rack_id: Optional[int] = Query(None, ge=1),
    book_items_filters: Dict = Depends(get_book_items_filters_from_query),
    book: BookInDB = Depends(get_book_by_id_from_path),
    books_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> ListOfBookItemsPublic:
    if library_id:
        book_items_filters["library_id"] = library_id
    if rack_id:
        book_items_filters["rack_id"] = rack_id
    book_items_filters["book_id"] = book.id
    return await books_items_repo.list_book_items(
        book_items_filters=book_items_filters,
        limit=PAGE_LIMIT,
        offset=(page - 1) * PAGE_LIMIT,
    )
