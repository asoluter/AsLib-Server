from typing import Optional, List

from pydantic import EmailStr
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from databases import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.models.profile import ProfileCreate
from app.models.user import (
    UserCreate,
    UserInDB,
    get_salted_password_update,
    UserUpdate,
)

GET_USER_BY_EMAIL_QUERY = """
    SELECT 
        id, 
        username, 
        email,
        email_verified, 
        password, 
        salt, 
        status, 
        role,
        library_card_number, 
        created_at, 
        updated_at
    FROM users
    WHERE email = :email;
"""

GET_USER_BY_USERNAME_QUERY = """
    SELECT
        id, 
        username, 
        email,
        email_verified, 
        password, 
        salt, 
        status, 
        role,
        library_card_number, 
        created_at, 
        updated_at
    FROM users
    WHERE username = :username;
"""

GET_USER_BY_ID_QUERY = """
    SELECT
        id, 
        username, 
        email,
        email_verified, 
        password, 
        salt, 
        status, 
        role,
        library_card_number, 
        created_at, 
        updated_at
    FROM users
    WHERE id = :id;
"""

GET_USER_BY_LIBRARY_CARD_NUMBER_QUERY = """
    SELECT
        id, 
        username, 
        email,
        email_verified, 
        password, 
        salt, 
        status, 
        role,
        library_card_number, 
        created_at, 
        updated_at
    FROM users
    WHERE library_card_number = :library_card_number;
"""

LIST_USERS_QUERY = """
    SELECT 
        id, 
        username, 
        email,
        email_verified, 
        password, 
        salt, 
        status, 
        role,
        library_card_number, 
        created_at, 
        updated_at
    FROM users
    ORDER BY users.id
    LIMIT :limit
    OFFSET :offset;
"""

COUNT_USER_ROWS_QUERY = """
    SELECT COUNT(*) FROM users;
"""

REGISTER_NEW_USER_QUERY = """
    INSERT INTO users (username, email, password, salt, role, status, library_card_number)
    VALUES (:username, :email, :password, :salt, :role, :status, :library_card_number)
    RETURNING
        id, 
        username, 
        email,
        email_verified, 
        password, 
        salt, 
        status, 
        role,
        library_card_number, 
        created_at, 
        updated_at;
"""


UPDATE_USER_QUERY = """
    UPDATE users
    SET email               = :email,
        email_verified      = :email_verified,
        password            = :password,
        salt                = :salt,
        status              = :status,
        role                = :role,
        library_card_number = :library_card_number
    WHERE id = :id
    RETURNING
        id, 
        username, 
        email,
        email_verified, 
        password, 
        salt, 
        status, 
        role,
        library_card_number, 
        created_at, 
        updated_at;
"""


class UsersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.profiles_repo = ProfilesRepository(db)

    async def get_user_by_email(self, *, email: EmailStr) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_EMAIL_QUERY, values={"email": email})
        if user_record:
            user = UserInDB(**user_record)
            return user

    async def get_user_by_username(self, *, username: str) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_USERNAME_QUERY, values={"username": username})
        if user_record:
            user = UserInDB(**user_record)
            return user

    async def get_user_by_id(self, *, id: int) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_ID_QUERY, values={"id": id})
        if user_record:
            user = UserInDB(**user_record)
            return user

    async def get_user_by_library_card_number(self, *, library_card_number: str) -> UserInDB:
        user_record = await self.db.fetch_one(
            query=GET_USER_BY_LIBRARY_CARD_NUMBER_QUERY, values={"library_card_number": library_card_number}
        )
        if user_record:
            user = UserInDB(**user_record)
            return user

    async def list_users(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> List[UserInDB]:
        user_records = await self.db.fetch_all(query=LIST_USERS_QUERY, values={"limit": limit, "offset": offset})
        return [UserInDB(**user_record) for user_record in user_records]

    async def users_count(self) -> int:
        cursor = await self.db.fetch_one(query=COUNT_USER_ROWS_QUERY)
        return cursor.get("count")

    async def register_new_user(self, *, new_user: UserCreate) -> UserInDB:
        # make sure email isn't already taken
        if await self.get_user_by_email(email=new_user.email):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="That email is already taken. Login with that email or register with another one.",
            )
        # make sure username isn't already taken
        if await self.get_user_by_username(username=new_user.username):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="That username is already taken. Please try another one.",
            )

        user_password_update = get_salted_password_update(new_user.password)
        new_user_params = new_user.copy(update=user_password_update.dict())
        created_user = await self.db.fetch_one(query=REGISTER_NEW_USER_QUERY, values=new_user_params.dict())

        # create profile for new user
        await self.profiles_repo.create_profile_for_user(profile_create=ProfileCreate(user_id=created_user["id"]))
        return UserInDB(**created_user)

    async def authenticate_user(self, *, username: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user_by_email(email=username)
        if not user:
            user = await self.get_user_by_username(username=username)
        if not user:
            return None
        # if submitted password doesn't match
        if not user.verify_password(password=password):
            return None
        return user

    async def update_user(self, *, user: UserInDB, user_update: UserUpdate) -> UserInDB:
        update_params = user.copy(update=user_update.dict(exclude_unset=True, exclude={"password"}))

        if user_update.password:
            update_params.change_password(user_update.password)

        if user_update.library_card_number and user_update.library_card_number != user.library_card_number:
            if await self.get_user_by_library_card_number(library_card_number=user_update.library_card_number):
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="That library card number is assigned to another user.",
                )

        if user_update.email and user_update.email != user.email:
            if await self.get_user_by_email(email=user_update.email):
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="That email is already taken.",
                )

        updated_user = await self.db.fetch_one(
            query=UPDATE_USER_QUERY,
            values=update_params.dict(exclude={"username", "created_at", "updated_at"}),
        )
        return UserInDB(**updated_user)
