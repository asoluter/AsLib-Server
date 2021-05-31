from app.db.repositories.base import BaseRepository
from app.models.profile import ProfileCreate, ProfileUpdate, ProfileInDB
from app.models.user import UserInDB

CREATE_PROFILE_FOR_USER_QUERY = """
    INSERT INTO profiles (first_name, surname, phone_number, bio, user_id)
    VALUES (:first_name, :surname, :phone_number, :bio, :user_id)
    RETURNING id, first_name, surname, phone_number, bio, user_id, created_at, updated_at;
"""

GET_PROFILE_BY_USER_ID_QUERY = """
    SELECT id, first_name, surname, phone_number, bio, user_id, created_at, updated_at
    FROM profiles
    WHERE user_id = :user_id;
"""

GET_PROFILE_BY_USERNAME_QUERY = """
    SELECT id,
           first_name,
           surname,
           phone_number,
           bio,
           user_id,
           created_at,
           updated_at
    FROM profiles
    WHERE user_id = (SELECT id FROM users WHERE username = :username);
"""

UPDATE_PROFILE_QUERY = """
    UPDATE profiles
    SET first_name   = :first_name,
        surname      = :surname,
        phone_number = :phone_number,
        bio          = :bio
    WHERE user_id = :user_id
    RETURNING id, first_name, surname, phone_number, bio, user_id, created_at, updated_at;
"""


class ProfilesRepository(BaseRepository):
    async def create_profile_for_user(self, *, profile_create: ProfileCreate) -> ProfileInDB:
        created_profile = await self.db.fetch_one(query=CREATE_PROFILE_FOR_USER_QUERY, values=profile_create.dict())
        return ProfileInDB(**created_profile)

    async def get_profile_by_user_id(self, *, user_id: int) -> ProfileInDB:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_USER_ID_QUERY, values={"user_id": user_id})
        if not profile_record:
            return None
        return ProfileInDB(**profile_record)

    async def get_profile_by_username(self, *, username: str) -> ProfileInDB:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_USERNAME_QUERY, values={"username": username})
        if profile_record:
            return ProfileInDB(**profile_record)

    async def update_profile(self, *, profile_update: ProfileUpdate, profile_owner: UserInDB) -> ProfileInDB:
        profile = await self.get_profile_by_user_id(user_id=profile_owner.id)
        update_params = profile.copy(update=profile_update.dict(exclude_unset=True))
        updated_profile = await self.db.fetch_one(
            query=UPDATE_PROFILE_QUERY,
            values=update_params.dict(exclude={"id", "created_at", "updated_at"}),
        )
        return ProfileInDB(**updated_profile)
