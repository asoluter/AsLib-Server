from datetime import date
from typing import Optional, List

from pydantic import constr

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin


isbn_regex = r"^(?:ISBN(?:-1[03])?:?●)?(?=[0-9X]{10}$|(?=(?:[0-9]+[-●]){3})[-●0-9X]{13}$|97[89][0-9]{10}$|(?=(?:[0-9]+[-●]){4})[-●0-9]{17}$)(?:97[89][-●]?)?[0-9]{1,5}[-●]?[0-9]+[-●]?[0-9]+[-●]?[0-9X]$"


class BookBase(CoreModel):
    isbn: Optional[constr(regex=isbn_regex)]
    title: Optional[str]
    description: Optional[str]
    publisher: Optional[str]
    page_count: Optional[int]
    publish_date: Optional[date]


class BookCreate(BookBase):
    title: str
    authors: Optional[List[str]]


class BookUpdate(BookBase):
    authors: Optional[List[str]]


class BookInDB(IDModelMixin, DateTimeModelMixin, BookBase):
    pass


class BookPublic(BookInDB):
    authors: List[str]


class ListOfBooksPublic(CoreModel):
    books: List[BookPublic]
    books_count: int
