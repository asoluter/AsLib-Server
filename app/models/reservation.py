from datetime import date
from enum import Enum
from typing import Optional, List

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class ReservationStatus(str, Enum):
    pending = "pending"
    waiting = "waiting"
    cancelled = "cancelled"
    completed = "completed"


class ReservationBase(CoreModel):
    book_id: Optional[int]
    library_id: Optional[int]
    user_id: Optional[int]
    status: Optional[ReservationStatus]
    book_item_id: Optional[int]
    due_date: Optional[date]


class ReservationCreateMy(CoreModel):
    book_id: int
    library_id: int


class ReservationCreate(ReservationCreateMy):
    user_id: int


class ReservationInDB(IDModelMixin, DateTimeModelMixin, ReservationBase):
    pass


class ReservationPublic(ReservationInDB):
    pass


class ListOfReservationsPublic(CoreModel):
    reservations: List[ReservationPublic]
    reservations_count: int
