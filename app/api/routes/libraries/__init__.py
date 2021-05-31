from fastapi import APIRouter

from app.api.routes.libraries.libraries import router as libraries_router
from app.api.routes.libraries.librarians import router as librarians_router


router = APIRouter()

router.include_router(libraries_router, tags=["libraries"])
router.include_router(librarians_router, prefix="/{library_id}/librarians", tags=["librarians"])
