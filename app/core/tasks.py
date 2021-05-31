from typing import Callable
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from app.db.repositories.reservations import ReservationsRepository
from app.db.repositories.users import UsersRepository
from app.db.tasks import connect_to_db, close_db_connection
from app.models.user import UserCreate, UserRole


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        await connect_to_db(app)
        user_repo = UsersRepository(app.state._db)
        if not await user_repo.get_user_by_username(username="admin"):
            await user_repo.register_new_user(
                new_user=UserCreate(
                    username="admin", email="admin@asoluter.com", password="adminpw", role=UserRole.admin
                )
            )

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app


def create_daily_cleanup_handler(app: FastAPI) -> Callable:
    @repeat_every(seconds=60 * 60 * 24)  # 1 day
    async def daily_cleanup() -> None:
        reservations_repo = ReservationsRepository(app.state._db)
        await reservations_repo.cancel_due_reservations()

    return daily_cleanup
