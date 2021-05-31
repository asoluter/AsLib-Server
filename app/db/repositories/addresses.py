from app.db.repositories.base import BaseRepository
from app.models.address import AddressUpdate, AddressInDB, AddressCreate
from app.models.library import LibraryInDB


CREATE_ADDRESS_QUERY = """
    INSERT INTO addresses (street_addr, city, state, zipcode, country)
    VALUES (:street_addr, :city, :state, :zipcode, :country)
    RETURNING id, street_addr, city, state, zipcode, country, created_at, updated_at;
"""

ASSIGN_ADDRESS_TO_LIBRARY_QUERY = """
    INSERT INTO libraries_to_addresses (library_id, address_id)
    VALUES (:library_id, :address_id);
"""

GET_ADDRESS_BY_ID_QUERY = """
    SELECT id, street_addr, city, state, zipcode, country, created_at, updated_at
    FROM addresses
    WHERE id = :id;
"""

GET_ADDRESS_BY_LIBRARY_ID_QUERY = """
    SELECT A.id, street_addr, city, state, zipcode, country, created_at, updated_at
    FROM addresses A
    INNER JOIN libraries_to_addresses LA ON A.id = LA.address_id
    WHERE LA.library_id = :library_id;
"""

UPDATE_ADDRESS_QUERY = """
    UPDATE addresses
    SET street_addr = :street_addr,
        city        = :city,
        state       = :state,
        zipcode     = :zipcode,
        country     = :country
    WHERE id = :id
    RETURNING id, street_addr, city, state, zipcode, country, created_at, updated_at;
"""

DELETE_ADDRESS_BY_ID_QUERY = """
    DELETE FROM addresses
    WHERE id = :id;
"""


class AddressesRepository(BaseRepository):
    async def create_address_for_library(self, *, address_create: AddressCreate, library: LibraryInDB) -> AddressInDB:
        async with self.db.transaction():
            created_address_record = await self.db.fetch_one(
                query=CREATE_ADDRESS_QUERY, values=address_create.dict(exclude={"library_id"})
            )
            created_address = AddressInDB(**created_address_record)
            await self.db.execute(
                query=ASSIGN_ADDRESS_TO_LIBRARY_QUERY,
                values={"library_id": library.id, "address_id": created_address.id},
            )
            return created_address

    async def get_address_by_id(self, *, id: int) -> AddressInDB:
        address_record = await self.db.fetch_one(query=GET_ADDRESS_BY_ID_QUERY, values={"id": id})
        if address_record:
            address = AddressInDB(**address_record)
            return address

    async def get_address_by_library_id(self, *, library_id: int) -> AddressInDB:
        address_record = await self.db.fetch_one(
            query=GET_ADDRESS_BY_LIBRARY_ID_QUERY, values={"library_id": library_id}
        )
        if address_record:
            address = AddressInDB(**address_record)
            return address

    async def update_library_address(self, *, library: LibraryInDB, address_update: AddressUpdate) -> AddressInDB:
        address = await self.get_address_by_library_id(library_id=library.id)
        update_params = address.copy(update=address_update.dict(exclude_unset=True))
        updated_address_record = await self.db.fetch_one(
            query=UPDATE_ADDRESS_QUERY,
            values=update_params.dict(exclude={"created_at", "updated_at"}),
        )
        return AddressInDB(**updated_address_record)

    async def delete_library_address(self, *, library: LibraryInDB) -> None:
        address = await self.get_address_by_library_id(library_id=library.id)
        await self.db.execute(query=DELETE_ADDRESS_BY_ID_QUERY, values={"id": address.id})
