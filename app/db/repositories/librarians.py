from fastapi import HTTPException, status

from app.db.repositories.base import BaseRepository
from app.models.librarians import ListOfLibrariansPublic, LibrarianPublic, LibrarianAssignment
from app.models.library import LibraryInDB
from app.models.user import UserStatus, UserInDB

GET_LIBRARIAN_ASSIGNMENT_BY_USER_ID_QUERY = """
    SELECT library_id, user_id
    FROM libraries_to_librarians
    WHERE user_id = :user_id;
"""

ASSIGN_LIBRARIAN_QUERY = """
    INSERT INTO libraries_to_librarians (library_id, user_id)
    VALUES (:library_id, :user_id);
"""

REMOVE_LIBRARIAN_ASSIGNMENTS_QUERY = """
    DELETE FROM libraries_to_librarians
    WHERE user_id = :user_id;
"""

LIST_LIBRARY_LIBRARIANS_QUERY = """
    SELECT U.id, U.username, P.first_name, P.surname
    FROM libraries_to_librarians LU
        INNER JOIN users U ON U.id = LU.user_id
        INNER JOIN profiles P ON P.user_id = U.id
    WHERE LU.library_id = :library_id
        AND U.status = :status
    ORDER BY
        P.first_name,
        P.surname,
        U.id;
"""


class LibrariansRepository(BaseRepository):
    async def list_library_librarians(self, *, library: LibraryInDB) -> ListOfLibrariansPublic:
        # List only active librarians
        librarian_records = await self.db.fetch_all(
            query=LIST_LIBRARY_LIBRARIANS_QUERY, values={"library_id": library.id, "status": UserStatus.active}
        )
        return ListOfLibrariansPublic(
            librarians=[LibrarianPublic(**librarian_record) for librarian_record in librarian_records]
        )

    async def get_librarian_assignment_by_user_id(self, *, user_id: int) -> LibrarianAssignment:
        assignment_record = await self.db.fetch_one(
            query=GET_LIBRARIAN_ASSIGNMENT_BY_USER_ID_QUERY, values={"user_id": user_id}
        )
        if assignment_record:
            return LibrarianAssignment(**assignment_record)

    async def assign_librarian(self, *, user: UserInDB, library: LibraryInDB):
        async with self.db.transaction():
            existing_assignment = await self.get_librarian_assignment_by_user_id(user_id=user.id)
            if existing_assignment:
                if existing_assignment.library_id == library.id:
                    return
                await self.remove_librarian_assignments(user=user)
            await self.db.execute(query=ASSIGN_LIBRARIAN_QUERY, values={"library_id": library.id, "user_id": user.id})

    async def remove_librarian_assignments(self, *, user: UserInDB):
        await self.db.execute(query=REMOVE_LIBRARIAN_ASSIGNMENTS_QUERY, values={"user_id": user.id})

    async def unassign_librarian(self, *, user: UserInDB, library: LibraryInDB):
        async with self.db.transaction():
            existing_assignment = await self.get_librarian_assignment_by_user_id(user_id=user.id)
            if not existing_assignment or existing_assignment.library_id != library.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Given user is not assigned to the selected library.",
                )
            await self.remove_librarian_assignments(user=user)
