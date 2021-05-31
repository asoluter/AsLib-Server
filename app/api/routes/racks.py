from typing import Optional, Dict

from fastapi import APIRouter, Depends, Body, Query

from app.api.dependencies.auth import get_current_active_user, get_current_active_user_with_permissions
from app.api.dependencies.book_items import get_book_items_filters_from_query
from app.api.dependencies.books import get_book_filters_from_query
from app.api.dependencies.database import get_repository
from app.api.dependencies.racks import get_rack_by_id_from_path
from app.core.config import PAGE_LIMIT
from app.db.repositories.book_items import BookItemsRepository
from app.db.repositories.books import BooksRepository
from app.db.repositories.racks import RacksRepository
from app.models.book import ListOfBooksPublic
from app.models.book_item import ListOfBookItemsPublic
from app.models.rack import RackPublic, RackInDB, RackUpdate
from app.models.user import UserInDB, UserRole

router = APIRouter()


@router.get("/{rack_id}/", response_model=RackPublic, name="racks:get-rack-by-id")
async def get_rack_by_id(
    rack: RackInDB = Depends(get_rack_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
) -> RackPublic:
    return rack


@router.put("/{rack_id}/", response_model=RackPublic, name="racks:update-rack-by-id")
async def update_rack(
    rack_update: RackUpdate = Body(..., embed=True),
    rack: RackInDB = Depends(get_rack_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    racks_repo: RacksRepository = Depends(get_repository(RacksRepository)),
) -> RackPublic:
    return await racks_repo.update_rack(rack=rack, rack_update=rack_update)


@router.delete("/{rack_id}/", name="racks:delete-rack-by-id")
async def delete_rack(
    rack: RackInDB = Depends(get_rack_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    racks_repo: RacksRepository = Depends(get_repository(RacksRepository)),
) -> None:
    await racks_repo.delete_rack(rack=rack)


@router.get("/{rack_id}/books/", response_model=ListOfBooksPublic, name="racks:list-rack-books")
async def list_library_books(
    page: int = Query(1, ge=1),
    book_filters: Dict = Depends(get_book_filters_from_query),
    rack: RackInDB = Depends(get_rack_by_id_from_path),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> ListOfBooksPublic:
    book_filters["rack_id"] = rack.id
    return await books_repo.list_books(book_filters=book_filters, limit=PAGE_LIMIT, offset=(page - 1) * PAGE_LIMIT)


@router.get("/{rack_id}/books/items", response_model=ListOfBookItemsPublic, name="racks:list-rack-book-items")
async def list_library_book_items(
    page: int = Query(1, ge=1),
    library_id: Optional[int] = Query(None, ge=1),
    book_items_filters: Dict = Depends(get_book_items_filters_from_query),
    rack: RackInDB = Depends(get_rack_by_id_from_path),
    book_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> ListOfBookItemsPublic:
    book_items_filters["rack_id"] = rack.id
    if library_id:
        book_items_filters["library_id"] = library_id
    return await book_items_repo.list_book_items(
        book_items_filters=book_items_filters, limit=PAGE_LIMIT, offset=(page - 1) * PAGE_LIMIT
    )
