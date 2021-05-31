from typing import Optional

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class ProfileBase(CoreModel):
    first_name: Optional[str]
    surname: Optional[str]
    phone_number: Optional[str]
    bio: Optional[str]


class ProfileCreate(ProfileBase):
    user_id: int


class ProfileUpdate(ProfileBase):
    pass


class ProfileInDB(IDModelMixin, DateTimeModelMixin, ProfileBase):
    user_id: int


class ProfilePublic(ProfileInDB):
    pass
