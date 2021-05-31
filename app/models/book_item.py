from typing import Optional, List
from enum import Enum

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin


class BookItemCondition(str, Enum):
    like_new = "like_new"
    good = "good"
    bad = "bad"


class BookItemManualStatus(str, Enum):
    available = "available"
    lost = "lost"
    written_off = "written_off"


class BookItemStatus(str, Enum):
    available = "available"
    lost = "lost"
    written_off = "written_off"
    reserved = "reserved"
    loaned = "loaned"


class BookItemBase(CoreModel):
    barcode: Optional[str]
    condition: Optional[BookItemCondition]
    library_id: Optional[int]
    rack_id: Optional[int]
    status: Optional[BookItemStatus]


class BookItemCreate(BookItemBase):
    barcode: str
    condition: BookItemCondition
    library_id: int
    status: BookItemManualStatus


class BookItemInternalUpdate(BookItemBase):
    pass


class BookItemUpdate(BookItemInternalUpdate):
    status: Optional[BookItemManualStatus]


class BookItemInDB(IDModelMixin, DateTimeModelMixin, BookItemBase):
    book_id: int


class BookItemPublic(BookItemInDB):
    pass


class ListOfBookItemsPublic(CoreModel):
    book_items: List[BookItemPublic]
    book_items_count: int
