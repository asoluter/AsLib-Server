from fastapi import APIRouter, Depends

from app.api.dependencies.database import get_repository
from app.db.repositories.authors import AuthorsRepository
from app.models.author import ListOfAuthors

router = APIRouter()


@router.get("", response_model=ListOfAuthors, name="authors:get-all")
async def get_all_authors(
    authors_repo: AuthorsRepository = Depends(get_repository(AuthorsRepository)),
) -> ListOfAuthors:
    authors = await authors_repo.get_all_authors()
    return ListOfAuthors(authors=authors)


@router.delete("", name="authors:delete-unused-authors")
async def delete_unused_authors(
    authors_repo: AuthorsRepository = Depends(get_repository(AuthorsRepository)),
) -> None:
    await authors_repo.delete_unused_authors()
