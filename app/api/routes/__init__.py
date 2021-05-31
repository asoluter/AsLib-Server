from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.libraries import router as libraries_router
from app.api.routes.racks import router as racks_router
from app.api.routes.authors import router as authors_router
from app.api.routes.books import router as books_router
from app.api.routes.book_items import router as book_items_router
from app.api.routes.reservations import router as reservations_router
from app.api.routes.lendings import router as lendings_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(libraries_router, prefix="/libraries", tags=["libraries"])
router.include_router(racks_router, prefix="/racks", tags=["racks"])
router.include_router(authors_router, prefix="/authors", tags=["authors"])
router.include_router(books_router, prefix="/books", tags=["books"])
router.include_router(book_items_router, prefix="/book_items", tags=["book_items"])
router.include_router(reservations_router, prefix="/reservations", tags=["reservations"])
router.include_router(lendings_router, prefix="/lendings", tags=["lendings"])
