"""create_main_tables

Revision ID: 8a9272ba5a3a
Revises: 
Create Date: 2021-05-09 16:53:26.487313

"""
from typing import Tuple

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "8a9272ba5a3a"
down_revision = None
branch_labels = None
depends_on = None


def create_updated_at_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )


def timestamps(indexed: bool = False) -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
    )


def create_system_config() -> None:
    op.create_table(
        "system_config",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("reservation_due_day", sa.Integer, server_default=sa.text("7"), nullable=False),
        sa.Column("lending_due_day", sa.Integer, server_default=sa.text("14"), nullable=False),
        sa.Column("lending_daily_fee", sa.Numeric, server_default=sa.text("5"), nullable=False),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_system_config_modtime
            BEFORE UPDATE
            ON system_config
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )
    op.execute(
        """
        INSERT INTO system_config (reservation_due_day, lending_due_day, lending_daily_fee)
         VALUES (DEFAULT, DEFAULT, DEFAULT);
        """
    )


def create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("password", sa.Text, nullable=False),
        sa.Column("salt", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("library_card_number", sa.Text, unique=True, nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_user_modtime
            BEFORE UPDATE
            ON users
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_profiles_table() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("first_name", sa.Text, nullable=True),
        sa.Column("surname", sa.Text, nullable=True),
        sa.Column("phone_number", sa.Text, nullable=True),
        sa.Column("bio", sa.Text, nullable=True, server_default=""),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_profiles_modtime
            BEFORE UPDATE
            ON profiles
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_addresses_table() -> None:
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("street_addr", sa.Text, nullable=True),
        sa.Column("city", sa.Text, nullable=True),
        sa.Column("state", sa.Text, nullable=True),
        sa.Column("zipcode", sa.Text, nullable=True),
        sa.Column("country", sa.Text, nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_addresses_modtime
            BEFORE UPDATE
            ON addresses
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_libraries_table() -> None:
    op.create_table(
        "libraries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_libraries_modtime
            BEFORE UPDATE
            ON libraries
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_libraries_to_addresses_table() -> None:
    op.create_table(
        "libraries_to_addresses",
        sa.Column(
            "library_id",
            sa.Integer,
            sa.ForeignKey("libraries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "address_id",
            sa.Integer,
            sa.ForeignKey("addresses.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_primary_key("pk_libraries_to_addresses", "libraries_to_addresses", ["library_id", "address_id"])


def create_libraries_to_librarians_table() -> None:
    op.create_table(
        "libraries_to_librarians",
        sa.Column(
            "library_id",
            sa.Integer,
            sa.ForeignKey("libraries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_primary_key("pk_libraries_to_librarians", "libraries_to_librarians", ["library_id", "user_id"])


def create_racks_table() -> None:
    op.create_table(
        "racks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=True),
        sa.Column("location_info", sa.Text, nullable=True),
        sa.Column("library_id", sa.Integer, sa.ForeignKey("libraries.id", ondelete="CASCADE")),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_racks_modtime
            BEFORE UPDATE
            ON racks
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_books_table() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("isbn", sa.Text, nullable=True, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("publisher", sa.Text, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("publish_date", sa.Date, nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_books_modtime
            BEFORE UPDATE
            ON books
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_authors_table() -> None:
    op.create_table(
        "authors",
        sa.Column("name", sa.Text, primary_key=True),
    )


def create_books_to_authors_table() -> None:
    op.create_table(
        "books_to_authors",
        sa.Column(
            "book_id",
            sa.Integer,
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_name",
            sa.Text,
            sa.ForeignKey("authors.name", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_primary_key("pk_books_to_authors", "books_to_authors", ["book_id", "author_name"])


def create_book_items_table() -> None:
    op.create_table(
        "book_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("barcode", sa.Text, nullable=False, unique=True),
        sa.Column("condition", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("books.id", ondelete="CASCADE")),
        sa.Column("library_id", sa.Integer, sa.ForeignKey("libraries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rack_id", sa.Integer, sa.ForeignKey("racks.id", ondelete="SET NULL"), nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_book_items_modtime
            BEFORE UPDATE
            ON book_items
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_reservations_table() -> None:
    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("books.id", ondelete="SET NULL"), nullable=True),
        sa.Column("library_id", sa.Integer, sa.ForeignKey("libraries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("book_item_id", sa.Integer, sa.ForeignKey("book_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_reservations_modtime
            BEFORE UPDATE
            ON book_items
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_lendings_table() -> None:
    op.create_table(
        "lendings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("book_item_id", sa.Integer, sa.ForeignKey("book_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reservation_id", sa.Integer, sa.ForeignKey("libraries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("return_date", sa.Date, nullable=True),
        sa.Column("fee", sa.Numeric, nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_lendings_modtime
            BEFORE UPDATE
            ON lendings
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def upgrade() -> None:
    create_updated_at_trigger()
    create_system_config()
    create_users_table()
    create_profiles_table()
    create_addresses_table()
    create_libraries_table()
    create_libraries_to_addresses_table()
    create_libraries_to_librarians_table()
    create_racks_table()
    create_books_table()
    create_authors_table()
    create_books_to_authors_table()
    create_book_items_table()
    create_reservations_table()
    create_lendings_table()


def downgrade() -> None:
    op.drop_table("lendings")
    op.drop_table("reservations")
    op.drop_table("book_items")
    op.drop_table("books_to_authors")
    op.drop_table("authors")
    op.drop_table("books")
    op.drop_table("racks")
    op.drop_table("libraries_to_librarians")
    op.drop_table("libraries_to_addresses")
    op.drop_table("libraries")
    op.drop_table("addresses")
    op.drop_table("profiles")
    op.drop_table("users")
    op.drop_table("system_config")
    op.execute("DROP FUNCTION update_updated_at_column")
