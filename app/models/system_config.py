from decimal import Decimal

from app.models.core import CoreModel, IDModelMixin, DateTimeModelMixin


class SystemConfig(CoreModel):
    reservation_due_day: int
    lending_due_day: int
    lending_daily_fee: Decimal


class SystemConfigUpdate(SystemConfig):
    pass


class SystemConfigInDB(IDModelMixin, DateTimeModelMixin, SystemConfig):
    pass


class SystemConfigPublic(DateTimeModelMixin, SystemConfig):
    pass
