from typing import List

from app.db.repositories.base import BaseRepository

CREATE_AUTHORS_THAT_DONT_EXIST_QUERY = """
    INSERT INTO authors (name)
    VALUES (:name)
    ON CONFLICT DO NOTHING;
"""

GET_ALL_AUTHORS_QUERY = """
    SELECT name
    FROM authors;
"""

DELETE_UNUSED_AUTHORS_QUERY = """
    DELETE FROM authors A
    WHERE NOT EXISTS (
        SELECT FROM books_to_authors BA
        WHERE A.name = BA.author_name
    );
"""


class AuthorsRepository(BaseRepository):
    async def get_all_authors(self) -> List[str]:
        author_rows = await self.db.fetch_all(query=GET_ALL_AUTHORS_QUERY)
        return [author.get("name") for author in author_rows]

    async def create_authors_that_dont_exist(self, *, authors: List[str]) -> None:
        await self.db.execute_many(
            query=CREATE_AUTHORS_THAT_DONT_EXIST_QUERY, values=[{"name": author} for author in authors]
        )

    async def delete_unused_authors(self) -> None:
        await self.db.execute(query=DELETE_UNUSED_AUTHORS_QUERY)
