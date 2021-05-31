from typing import List, Optional

from app.models.core import CoreModel, IDModelMixin


class LibrarianAssignment(CoreModel):
    library_id: int
    user_id: int


class LibrarianPublic(IDModelMixin, CoreModel):
    username: str
    first_name: Optional[str]
    surname: Optional[str]


class ListOfLibrariansPublic(CoreModel):
    librarians: List[LibrarianPublic]
