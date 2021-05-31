from datetime import date
from decimal import Decimal
from typing import Optional, List

from app.models.core import DateTimeModelMixin, CoreModel, IDModelMixin


class LendingBase(CoreModel):
    user_id: Optional[int]
    book_item_id: Optional[int]
    reservation_id: Optional[int]
    due_date: Optional[date]
    return_date: Optional[date]
    fee: Optional[Decimal] = 0


class LendingCreate(CoreModel):
    user_id: int
    book_item_id: int


class LendingInDB(IDModelMixin, DateTimeModelMixin, LendingBase):
    pass


class LendingPublic(LendingInDB):
    pass


class ListOfLendingsPublic(CoreModel):
    lendings: List[LendingPublic]
    lendings_count: int
