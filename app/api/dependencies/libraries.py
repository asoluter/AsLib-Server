from fastapi import Path, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.users import get_user_by_id_from_query
from app.db.repositories.libraries import LibrariesRepository
from app.models.library import LibraryInDB
from app.models.user import UserInDB, UserRole


async def get_library_by_id_from_path(
    library_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    libraries_repo: LibrariesRepository = Depends(get_repository(LibrariesRepository)),
) -> LibraryInDB:
    library = await libraries_repo.get_library_by_id(id=library_id, populate=False)
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No library found with that id.",
        )
    return library


async def get_librarian_by_id_from_query(
    user: UserInDB = Depends(get_user_by_id_from_query),
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    if user.role != UserRole.librarian:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Given user is not a librarian.")
    return user
