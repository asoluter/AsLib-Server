from typing import Optional, List

from app.models.address import AddressPublic, AddressCreate, AddressUpdate
from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class LibraryBase(CoreModel):
    name: Optional[str]
    description: Optional[str]


class LibraryCreate(LibraryBase):
    address: Optional[AddressCreate]


class LibraryUpdate(LibraryBase):
    address: Optional[AddressUpdate]


class LibraryInDB(IDModelMixin, DateTimeModelMixin, LibraryBase):
    pass


class LibraryPublic(LibraryInDB):
    address: Optional[AddressPublic]


class ListOfLibrariesPublic(CoreModel):
    libraries: List[LibraryPublic]
    libraries_count: int
