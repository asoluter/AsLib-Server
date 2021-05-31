from typing import Dict, Optional

from fastapi import APIRouter, status, Body, Depends, Query

from app.api.dependencies.book_items import get_book_items_filters_from_query
from app.api.dependencies.books import get_book_filters_from_query

from app.api.dependencies.auth import get_current_active_user_with_permissions, get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.libraries import get_library_by_id_from_path
from app.core.config import PAGE_LIMIT
from app.db.repositories.book_items import BookItemsRepository
from app.db.repositories.books import BooksRepository
from app.db.repositories.libraries import LibrariesRepository
from app.db.repositories.racks import RacksRepository
from app.models.book import ListOfBooksPublic
from app.models.book_item import ListOfBookItemsPublic
from app.models.library import LibraryPublic, LibraryCreate, ListOfLibrariesPublic, LibraryInDB, LibraryUpdate
from app.models.rack import ListOfRacksPublic, RackPublic, RackCreate
from app.models.user import UserInDB, UserRole

router = APIRouter()


@router.post("/", response_model=LibraryPublic, name="libraries:create-library", status_code=status.HTTP_201_CREATED)
async def create_new_library(
    new_library: LibraryCreate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.admin)),
    libraries_repo: LibrariesRepository = Depends(get_repository(LibrariesRepository)),
) -> LibraryPublic:
    return await libraries_repo.create_library(new_library=new_library)


@router.get("/", response_model=ListOfLibrariesPublic, name="libraries:list-libraries")
async def list_libraries(
    page: int = Query(1, ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    libraries_repo: LibrariesRepository = Depends(get_repository(LibrariesRepository)),
) -> ListOfLibrariesPublic:
    return ListOfLibrariesPublic(
        libraries=await libraries_repo.list_libraries(limit=PAGE_LIMIT, offset=(page - 1) * PAGE_LIMIT),
        libraries_count=await libraries_repo.libraries_count(),
    )


@router.get("/{library_id}/", response_model=LibraryPublic, name="libraries:get-library-by-id")
async def get_library_by_id(
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    libraries_repo: LibrariesRepository = Depends(get_repository(LibrariesRepository)),
) -> LibraryPublic:
    return await libraries_repo.populate_library(library=library)


@router.put(
    "/{library_id}/",
    response_model=LibraryPublic,
    name="libraries:update-library-by-id",
)
async def update_library_by_id(
    library_update: LibraryUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    libraries_repo: LibrariesRepository = Depends(get_repository(LibrariesRepository)),
) -> LibraryPublic:
    return await libraries_repo.update_library(library=library, library_update=library_update)


@router.delete(
    "/{library_id}/",
    name="libraries:delete-library-by-id",
)
async def delete_library_by_id(
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.admin)),
    libraries_repo: LibrariesRepository = Depends(get_repository(LibrariesRepository)),
) -> None:
    await libraries_repo.delete_library(library=library)


@router.get("/{library_id}/racks/", response_model=ListOfRacksPublic, name="libraries:list-library-racks")
async def list_library_racks(
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
    racks_repo: RacksRepository = Depends(get_repository(RacksRepository)),
) -> ListOfRacksPublic:
    return ListOfRacksPublic(
        racks=await racks_repo.list_library_racks(library=library),
    )


@router.post(
    "/{library_id}/racks/", response_model=RackPublic, name="libraries:create-rack", status_code=status.HTTP_201_CREATED
)
async def create_rack(
    new_rack: RackCreate = Body(..., embed=True),
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    racks_repo: RacksRepository = Depends(get_repository(RacksRepository)),
) -> RackPublic:
    return await racks_repo.create_rack_for_library(library=library, new_rack=new_rack)


@router.get("/{library_id}/books/", response_model=ListOfBooksPublic, name="libraries:list-library-books")
async def list_library_books(
    page: int = Query(1, ge=1),
    book_filters: Dict = Depends(get_book_filters_from_query),
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> ListOfBooksPublic:
    book_filters["library_id"] = library.id
    return await books_repo.list_books(book_filters=book_filters, limit=PAGE_LIMIT, offset=(page - 1) * PAGE_LIMIT)


@router.get("/{library_id}/books/items", response_model=ListOfBookItemsPublic, name="libraries:list-library-book-items")
async def list_library_book_items(
    page: int = Query(1, ge=1),
    rack_id: Optional[int] = Query(None, ge=1),
    book_items_filters: Dict = Depends(get_book_items_filters_from_query),
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    book_items_repo: BookItemsRepository = Depends(get_repository(BookItemsRepository)),
) -> ListOfBookItemsPublic:
    book_items_filters["library_id"] = library.id
    if rack_id:
        book_items_filters["rack_id"] = rack_id
    return await book_items_repo.list_book_items(
        book_items_filters=book_items_filters, limit=PAGE_LIMIT, offset=(page - 1) * PAGE_LIMIT
    )
