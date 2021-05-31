from fastapi import APIRouter, Depends, Body

from app.api.dependencies.auth import get_current_active_user_with_permissions
from app.api.dependencies.book_items import get_book_item_by_id_from_path
from app.api.dependencies.database import get_repository
from app.db.repositories.book_items import BookItemsRepository
from app.models.book_item import BookItemPublic, BookItemInDB, BookItemUpdate, BookItemStatus
from app.models.user import UserInDB, UserRole

router = APIRouter()


@router.get("/barcode/{barcode}", response_model=BookItemPublic, name="book-items:get-book-item-by-id")
async def get_book_item_by_barcode(
    book_item: BookItemInDB = Depends(get_book_item_by_id_from_path),
) -> BookItemPublic:
    return book_item


@router.get("/{book_item_id}/", response_model=BookItemPublic, name="book-items:get-book-item-by-id")
async def get_book_item_by_id(
    book_item: BookItemInDB = Depends(get_book_item_by_id_from_path),
) -> BookItemPublic:
    return book_item


@router.put(
    "/{book_item_id}/",
    response_model=BookItemPublic,
    name="book-items:update-book-item-by-id",
)
async def update_book_item_by_id(
    book_item_update: BookItemUpdate = Body(..., embed=True),
    book_item: BookItemInDB = Depends(get_book_item_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    books_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> BookItemPublic:
    if book_item_update.status == BookItemStatus.available and book_item.status not in {
        BookItemStatus.lost,
        BookItemStatus.written_off,
    }:
        book_item_update.status = book_item.status
    return await books_items_repo.update_book_item(book_item=book_item, book_item_update=book_item_update)


@router.delete(
    "/{book_item_id}/",
    name="book-items:delete-book-item-by-id",
)
async def delete_book_by_id(
    book_item: BookItemInDB = Depends(get_book_item_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    books_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> None:
    return await books_items_repo.delete_book_item(book_item=book_item)
