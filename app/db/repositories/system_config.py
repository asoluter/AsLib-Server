from app.db.repositories.base import BaseRepository
from app.models.system_config import SystemConfigInDB, SystemConfigUpdate


GET_SYSTEM_CONFIG_QUERY = """
    SELECT id, reservation_due_day, lending_due_day, lending_daily_fee, created_at, updated_at
    FROM system_config;
"""

UPDATE_SYSTEM_CONFIG_QUERY = """
    UPDATE system_config
    SET reservation_due_day = :reservation_due_day,
        lending_due_day = :lending_due_day,
        lending_daily_fee = :lending_daily_fee
    RETURNING id, reservation_due_day, lending_due_day, lending_daily_fee, created_at, updated_at;
"""


class SystemConfigRepository(BaseRepository):
    async def get_config(self) -> SystemConfigInDB:
        system_config_record = await self.db.fetch_one(query=GET_SYSTEM_CONFIG_QUERY)
        return SystemConfigInDB(**system_config_record)

    async def update_config(self, system_config_update: SystemConfigUpdate) -> SystemConfigInDB:
        updated_system_config_record = await self.db.fetch_one(
            query=UPDATE_SYSTEM_CONFIG_QUERY, values=system_config_update.dict()
        )
        return SystemConfigInDB(**updated_system_config_record)
