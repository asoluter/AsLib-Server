from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import get_current_active_user, get_current_active_user_with_permissions
from app.api.dependencies.database import get_repository
from app.api.dependencies.libraries import get_library_by_id_from_path, get_librarian_by_id_from_query
from app.db.repositories.librarians import LibrariansRepository
from app.models.librarians import ListOfLibrariansPublic
from app.models.library import LibraryInDB
from app.models.user import UserInDB, UserRole

router = APIRouter()


@router.get("/", response_model=ListOfLibrariansPublic, name="libraries:list-assigned-librarians")
async def list_assigned_librarians(
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
    librarians_repo: LibrariansRepository = Depends(get_repository(LibrariansRepository)),
) -> ListOfLibrariansPublic:
    return await librarians_repo.list_library_librarians(library=library)


@router.put("/", name="libraries:assign-librarian-by-id", status_code=status.HTTP_202_ACCEPTED)
async def assign_librarian(
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    librarian: UserInDB = Depends(get_librarian_by_id_from_query),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.admin)),
    librarians_repo: LibrariansRepository = Depends(get_repository(LibrariansRepository)),
) -> None:
    await librarians_repo.assign_librarian(library=library, user=librarian)


@router.delete(
    "/",
    name="libraries:unassign-librarian-by-id",
)
async def unassign_librarian(
    library: LibraryInDB = Depends(get_library_by_id_from_path),
    librarian: UserInDB = Depends(get_librarian_by_id_from_query),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.admin)),
    librarians_repo: LibrariansRepository = Depends(get_repository(LibrariansRepository)),
) -> None:
    await librarians_repo.unassign_librarian(library=library, user=librarian)
