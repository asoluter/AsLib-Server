from typing import List

from app.models.core import CoreModel


class ListOfAuthors(CoreModel):
    authors: List[str]
