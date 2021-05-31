from typing import Optional

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class AddressBase(CoreModel):
    street_addr: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zipcode: Optional[str]
    country: Optional[str]


class AddressCreate(AddressBase):
    pass


class AddressUpdate(AddressBase):
    pass


class AddressInDB(IDModelMixin, DateTimeModelMixin, AddressBase):
    pass


class AddressPublic(AddressInDB):
    pass
