from fastapi import APIRouter, Body, Depends

from app.api.dependencies.auth import get_current_active_user, get_current_active_user_with_permissions
from app.api.dependencies.database import get_repository
from app.api.dependencies.users import get_user_by_username_from_path
from app.db.repositories.profiles import ProfilesRepository
from app.models.profile import ProfileUpdate, ProfilePublic
from app.models.user import UserInDB, UserRole

router = APIRouter()


@router.get("/me/", response_model=ProfilePublic, name="profiles:get-own-profile")
async def get_profile_by_username(
    current_user: UserInDB = Depends(get_current_active_user),
    profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
) -> ProfilePublic:
    return await profiles_repo.get_profile_by_user_id(user_id=current_user.id)


@router.put("/me/", response_model=ProfilePublic, name="profiles:update-own-profile")
async def update_own_profile(
    profile_update: ProfileUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user),
    profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
) -> ProfilePublic:
    return await profiles_repo.update_profile(profile_update=profile_update, profile_owner=current_user)


@router.get("/{username}/", response_model=ProfilePublic, name="profiles:get-profile-by-username")
async def get_profile_by_username(
    user: UserInDB = Depends(get_user_by_username_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
    profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
) -> ProfilePublic:
    return await profiles_repo.get_profile_by_user_id(user_id=user.id)


@router.put("/{username}/", response_model=ProfilePublic, name="profiles:update-user-profile")
async def update_user_profile(
    profile_update: ProfileUpdate = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_active_user_with_permissions(UserRole.admin)),
    user: UserInDB = Depends(get_user_by_username_from_path),
    profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
) -> ProfilePublic:
    return await profiles_repo.update_profile(profile_update=profile_update, profile_owner=user)
