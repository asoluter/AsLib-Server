from enum import Enum
from typing import Optional, List
from pydantic import EmailStr, constr

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel
from app.services import security


class UserRole(str, Enum):
    default = "default"
    librarian = "librarian"
    admin = "admin"

    @classmethod
    def get_numeric_value(cls, item) -> int:
        mapping = {
            cls.default: 0,
            cls.librarian: 99,
            cls.admin: 999,
        }
        return mapping.get(item, 0)


class UserStatus(str, Enum):
    active = "active"
    deactivated = "deactivated"
    blacklisted = "blacklisted"


class UserBase(CoreModel):
    email: Optional[EmailStr]
    username: Optional[str]
    email_verified: bool = False
    role: Optional[UserRole] = UserRole.default
    status: Optional[UserStatus] = UserStatus.active
    library_card_number: Optional[str]


class UserCreate(CoreModel):
    email: EmailStr
    password: constr(min_length=7, max_length=100)
    username: constr(min_length=3, regex="^[a-zA-Z0-9_-]+$")
    role: Optional[UserRole] = UserRole.default
    status: Optional[UserStatus] = UserStatus.active
    library_card_number: Optional[constr(min_length=7, max_length=14, regex="^[0-9]+$")]


class CurrentUserUpdate(CoreModel):
    email: Optional[EmailStr]
    password: Optional[constr(min_length=7, max_length=100)]


class UserUpdate(CurrentUserUpdate):
    email: Optional[EmailStr]
    password: Optional[constr(min_length=7, max_length=100)]
    role: Optional[UserRole]
    status: Optional[UserStatus]
    library_card_number: Optional[constr(min_length=7, max_length=14, regex="^[0-9]+$")]


class UserPasswordUpdate(CoreModel):
    password: constr(min_length=7, max_length=100)
    salt: str


def get_salted_password_update(password: str) -> UserPasswordUpdate:
    salt = security.generate_salt()
    hashed_pw = security.hash_password(password=password, salt=salt)
    return UserPasswordUpdate(password=hashed_pw, salt=salt)


class UserInDB(IDModelMixin, DateTimeModelMixin, UserPasswordUpdate, UserBase):
    password: constr(min_length=7, max_length=100)
    salt: str

    def verify_password(self, password: str) -> bool:
        return security.verify_password(password=password, salt=self.salt, hashed_pw=self.password)

    def change_password(self, password: str) -> None:
        update = get_salted_password_update(password)
        self.salt = update.salt
        self.password = update.password


class UserPublic(IDModelMixin, DateTimeModelMixin, UserBase):
    pass


class ListOfUsersPublic(CoreModel):
    users: List[UserPublic]
    users_count: int
