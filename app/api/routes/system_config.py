from fastapi import APIRouter, Depends, Body

from app.api.dependencies.auth import get_current_active_user_with_permissions
from app.api.dependencies.database import get_repository
from app.db.repositories.system_config import SystemConfigRepository
from app.models.system_config import SystemConfigPublic, SystemConfigUpdate
from app.models.user import UserRole, UserInDB

router = APIRouter()


@router.get(
    "/",
    response_model=SystemConfigPublic,
    name="system-config:get-configuration",
)
async def get_config(
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.librarian)),
    system_config_repo: SystemConfigRepository = Depends(get_repository(SystemConfigRepository)),
) -> SystemConfigPublic:
    return await system_config_repo.get_config()


@router.put("/", response_model=SystemConfigPublic, name="system-config:update-configuration")
async def update_config(
    system_config_update: SystemConfigUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.admin)),
    system_config_repo: SystemConfigRepository = Depends(get_repository(SystemConfigRepository)),
) -> SystemConfigPublic:
    return await system_config_repo.update_config(system_config_update=system_config_update)
