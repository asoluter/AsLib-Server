from fastapi import Path, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.addresses import AddressesRepository
from app.models.address import AddressInDB
from app.models.user import UserInDB


async def get_address_by_id_from_path(
    address_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    addresses_repo: AddressesRepository = Depends(get_repository(AddressesRepository)),
) -> AddressInDB:
    address = await addresses_repo.get_address_by_id(id=address_id)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No address found with that id.",
        )
    return address
