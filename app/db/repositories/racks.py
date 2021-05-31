from typing import List

from app.db.repositories.base import BaseRepository
from app.models.library import LibraryInDB
from app.models.rack import RackCreate, RackInDB, RackUpdate

CREATE_RACK_QUERY = """
    INSERT INTO racks (name, location_info, library_id)
    VALUES (:name, :location_info, :library_id)
    RETURNING id, name, location_info, library_id, created_at, updated_at;
"""

GET_RACK_BY_ID_QUERY = """
    SELECT id, name, location_info, library_id, created_at, updated_at
    FROM racks
    WHERE id = :id;
"""

LIST_LIBRARY_RACKS_QUERY = """
    SELECT id, name, location_info, library_id, created_at, updated_at
    FROM racks
    WHERE library_id = :library_id;
"""

UPDATE_RACK_QUERY = """
    UPDATE racks
    SET name          = :name,
        location_info = :location_info
    WHERE id = :id
    RETURNING id, name, location_info, library_id, created_at, updated_at;
"""

DELETE_RACK_BY_ID_QUERY = """
    DELETE FROM racks
    WHERE id = :id;
"""


class RacksRepository(BaseRepository):
    async def create_rack_for_library(self, *, library: LibraryInDB, new_rack: RackCreate) -> RackInDB:
        created_rack_record = await self.db.fetch_one(
            query=CREATE_RACK_QUERY,
            values={"library_id": library.id, **new_rack.dict()},
        )
        return RackInDB(**created_rack_record)

    async def get_rack_by_id(self, *, id: int) -> RackInDB:
        rack_record = await self.db.fetch_one(query=GET_RACK_BY_ID_QUERY, values={"id": id})
        if rack_record:
            rack = RackInDB(**rack_record)
            return rack

    async def list_library_racks(self, *, library: LibraryInDB) -> List[RackInDB]:
        rack_records = await self.db.fetch_all(query=LIST_LIBRARY_RACKS_QUERY, values={"library_id": library.id})
        return [RackInDB(**rack_record) for rack_record in rack_records]

    async def update_rack(self, *, rack: RackInDB, rack_update: RackUpdate) -> RackInDB:
        update_params = rack.copy(update=rack_update.dict(exclude_unset=True))
        updated_rack_record = await self.db.fetch_one(
            query=UPDATE_RACK_QUERY,
            values=update_params.dict(exclude={"created_at", "updated_at", "library_id"}),
        )
        return RackInDB(**updated_rack_record)

    async def delete_rack(self, *, rack: RackInDB) -> None:
        await self.db.execute(query=DELETE_RACK_BY_ID_QUERY, values={"id": rack.id})
