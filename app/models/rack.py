from typing import Optional, List

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class RackBase(CoreModel):
    name: Optional[str]
    location_info: Optional[str]


class RackCreate(RackBase):
    pass


class RackUpdate(RackBase):
    pass


class RackInDB(IDModelMixin, DateTimeModelMixin, RackBase):
    library_id: int


class RackPublic(RackInDB):
    pass


class RackPublicWithoutLibraryId(IDModelMixin, DateTimeModelMixin, RackBase):
    pass


class ListOfRacksPublic(CoreModel):
    racks: List[RackPublicWithoutLibraryId]
