from fastapi import Depends, status, HTTPException, Path, Query

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.racks import RacksRepository
from app.models.rack import RackInDB
from app.models.user import UserInDB


async def get_rack_by_id_from_path(
    rack_id: int = Path(..., ge=1),
    current_user: UserInDB = Depends(get_current_active_user),
    racks_repo: RacksRepository = Depends(get_repository(RacksRepository)),
) -> RackInDB:
    rack = await racks_repo.get_rack_by_id(id=rack_id)
    if not rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No rack found with that id.",
        )
    return rack
