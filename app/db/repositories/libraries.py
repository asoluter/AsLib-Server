from typing import List

from databases import Database

from app.db.repositories.addresses import AddressesRepository
from app.db.repositories.base import BaseRepository
from app.models.address import AddressCreate
from app.models.library import LibraryInDB, LibraryPublic, LibraryCreate, LibraryUpdate

CREATE_LIBRARY_QUERY = """
    INSERT INTO libraries (name, description)
    VALUES (:name, :description)
    RETURNING id, name, description, created_at, updated_at;
"""

GET_LIBRARY_BY_ID_QUERY = """
    SELECT id, name, description, created_at, updated_at
    FROM libraries
    WHERE id = :id;
"""

LIST_LIBRARIES_QUERY = """
    SELECT 
        id, 
        name,
        description, 
        created_at, 
        updated_at
    FROM libraries
    ORDER BY libraries.id
    LIMIT :limit
    OFFSET :offset;
"""

COUNT_LIBRARY_ROWS_QUERY = """
    SELECT COUNT(*) FROM libraries;
"""

UPDATE_LIBRARY_BY_ID_QUERY = """
    UPDATE libraries
    SET name         = :name,
        description  = :description
    WHERE id = :id
    RETURNING id, name, description, created_at, updated_at;
"""

DELETE_LIBRARY_BY_ID_QUERY = """
    DELETE FROM libraries
    WHERE id = :id;
"""


class LibrariesRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.addresses_repo = AddressesRepository(db)

    async def create_library(self, *, new_library: LibraryCreate) -> LibraryPublic:
        async with self.db.transaction():
            created_library_record = await self.db.fetch_one(
                query=CREATE_LIBRARY_QUERY, values=new_library.dict(exclude={"address"})
            )
            created_library = LibraryInDB(**created_library_record)
            if not new_library.address:
                new_library.address = AddressCreate()
            await self.addresses_repo.create_address_for_library(
                address_create=new_library.address, library=created_library
            )
            return await self.populate_library(library=created_library)

    async def get_library_by_id(self, *, id: int, populate: bool = True) -> LibraryInDB:
        library_record = await self.db.fetch_one(query=GET_LIBRARY_BY_ID_QUERY, values={"id": id})
        if library_record:
            library = LibraryInDB(**library_record)
            if populate:
                return await self.populate_library(library=library)
            return library

    async def list_libraries(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        populate: bool = True,
    ) -> List[LibraryInDB]:
        library_records = await self.db.fetch_all(query=LIST_LIBRARIES_QUERY, values={"limit": limit, "offset": offset})
        if populate:
            return [
                await self.populate_library(library=LibraryInDB(**library_record)) for library_record in library_records
            ]
        return [LibraryInDB(**library_record) for library_record in library_records]

    async def libraries_count(self):
        cursor = await self.db.fetch_one(query=COUNT_LIBRARY_ROWS_QUERY)
        return cursor.get("count")

    async def update_library(self, *, library: LibraryInDB, library_update: LibraryUpdate) -> LibraryPublic:
        async with self.db.transaction():
            update_params = library.copy(update=library_update.dict(exclude_unset=True, exclude={"address"}))
            updated_library_record = await self.db.fetch_one(
                query=UPDATE_LIBRARY_BY_ID_QUERY,
                values=update_params.dict(exclude={"created_at", "updated_at"}),
            )
            updated_library = LibraryInDB(**updated_library_record)
            if library_update.address:
                await self.addresses_repo.update_library_address(
                    library=updated_library, address_update=library_update.address
                )
            return await self.populate_library(library=updated_library)

    async def delete_library(self, *, library: LibraryInDB):
        async with self.db.transaction():
            await self.addresses_repo.delete_library_address(library=library)
            await self.db.execute(query=DELETE_LIBRARY_BY_ID_QUERY, values={"id": library.id})

    async def populate_library(self, *, library: LibraryInDB) -> LibraryPublic:
        return LibraryPublic(
            **library.dict(),
            address=await self.addresses_repo.get_address_by_library_id(library_id=library.id),
        )
