from typing import Callable

import pytest

from databases import Database

from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.user import UserInDB, UserPublic
from app.models.profile import ProfileInDB, ProfilePublic
from app.db.repositories.profiles import ProfilesRepository


pytestmark = pytest.mark.asyncio


class TestProfileRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient, test_user: UserInDB) -> None:
        # Get profile by username
        res = await client.get(app.url_path_for("profiles:get-profile-by-username", username=test_user.username))
        assert res.status_code != status.HTTP_404_NOT_FOUND

        # Update own profile
        res = await client.put(app.url_path_for("profiles:update-own-profile"), json={"profile_update": {}})
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestProfileCreate:
    async def test_profile_created_for_new_users(
        self, app: FastAPI, create_authorized_client: Callable, test_librarian: UserInDB, db: Database
    ) -> None:
        authorized_client = create_authorized_client(user=test_librarian)
        profiles_repo = ProfilesRepository(db)

        new_user = {"email": "dwayne@johnson.io", "username": "therock", "password": "dwaynetherockjohnson"}
        res = await authorized_client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status.HTTP_201_CREATED

        created_user = UserPublic(**res.json())
        user_profile = await profiles_repo.get_profile_by_user_id(user_id=created_user.id)
        assert user_profile is not None
        assert isinstance(user_profile, ProfileInDB)


class TestProfileView:
    async def test_authenticated_user_can_view_other_users_profile(
        self, app: FastAPI, authorized_client: AsyncClient, test_user: UserInDB, test_user2: UserInDB
    ) -> None:
        res = await authorized_client.get(
            app.url_path_for("profiles:get-profile-by-username", username=test_user2.username)
        )
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert profile.user_id == test_user2.id

    async def test_unregistered_users_cannot_access_other_users_profile(
        self, app: FastAPI, client: AsyncClient, test_user2: UserInDB
    ) -> None:
        res = await client.get(app.url_path_for("profiles:get-profile-by-username", username=test_user2.username))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_no_profile_is_returned_when_username_matches_no_user(
        self, app: FastAPI, authorized_client: AsyncClient
    ) -> None:
        res = await authorized_client.get(
            app.url_path_for("profiles:get-profile-by-username", username="username_doesnt_match")
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND


class TestProfileManagement:
    @pytest.mark.parametrize(
        "attr, value",
        (
            ("first_name", "Lebron"),
            ("surname", "James"),
            ("phone_number", "555-333-1000"),
            ("bio", "This is a test bio"),
        ),
    )
    async def test_user_can_update_own_profile(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        attr: str,
        value: str,
    ) -> None:
        res = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"),
            json={"profile_update": {attr: value}},
        )
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert getattr(profile, attr) == value

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("first_name", [], 422),
            ("bio", {}, 422),
        ),
    )
    async def test_user_recieves_error_for_invalid_update_params(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        attr: str,
        value: str,
        status_code: int,
    ) -> None:
        res = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"),
            json={"profile_update": {attr: value}},
        )
        assert res.status_code == status_code
