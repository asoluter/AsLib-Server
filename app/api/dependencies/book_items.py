from typing import Optional, Dict

from fastapi import Path, Depends, HTTPException, status, Query

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.book_items import BookItemsRepository
from app.models.book_item import BookItemInDB, BookItemCondition, BookItemStatus
from app.models.user import UserInDB


async def get_book_item_by_id_from_path(
    book_item_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    book_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> BookItemInDB:
    book_item = await book_items_repo.get_book_item_by_id(id=book_item_id)
    if not book_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book item found with that id.",
        )
    return book_item


async def get_book_item_by_barcode_from_path(
    barcode: str = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    book_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> BookItemInDB:
    book_item = await book_items_repo.get_book_item_by_barcode(barcode=barcode)
    if not book_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book item found with that barcode.",
        )
    return book_item


async def get_book_item_by_id_from_query(
    book_item_id: int = Query(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    book_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> BookItemInDB:
    book_item = await book_items_repo.get_book_item_by_id(id=book_item_id)
    if not book_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book item found with that id.",
        )
    return book_item


async def get_book_items_filters_from_query(
    condition: Optional[BookItemCondition] = Query(None),
    status: Optional[BookItemStatus] = Query(None),
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict:
    book_items_filters = {}

    if condition:
        book_items_filters["condition"] = condition
    if status:
        book_items_filters["status"] = status

    return book_items_filters
