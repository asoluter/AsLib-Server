from datetime import date
from typing import Dict, Optional

from fastapi import Path, Depends, HTTPException, status, Query

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.books import BooksRepository
from app.models.book import BookInDB
from app.models.user import UserInDB


async def get_book_by_id_from_path(
    book_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    books_repo: BooksRepository = Depends(get_repository(BooksRepository)),
) -> BookInDB:
    book = await books_repo.get_book_by_id(id=book_id, populate=False)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No book found with that id.",
        )
    return book


async def get_book_filters_from_query(
    inisbn: Optional[str] = Query(None, max_length=50),
    intitle: Optional[str] = Query(None, max_length=50),
    inpublisher: Optional[str] = Query(None, max_length=50),
    inauthor: Optional[str] = Query(None, max_length=50),
    publish_date: Optional[date] = Query(None),
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict:
    book_filters = {}

    if inisbn:
        book_filters["inisbn"] = f"%{inisbn}%"
    if inauthor:
        book_filters["inauthor"] = f"%{inauthor}%"
    if intitle:
        book_filters["intitle"] = f"%{intitle}%"
    if inpublisher:
        book_filters["inpublisher"] = f"%{inpublisher}%"
    if publish_date:
        book_filters["publish_date"] = publish_date

    return book_filters
