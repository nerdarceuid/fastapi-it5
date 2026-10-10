"""SQLite connection and table setup."""
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DATABASE_FILE = Path(__file__).resolve().parent.parent / "equipment.db"

@contextmanager

def database_connection() -> Iterator[sqlite3.Connection]:

    connection = sqlite3.connect(DATABASE_FILE)

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def initialize_database() -> None:
    """Create the tables the first time the app runs."""

    with database_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
                    CHECK (length(name) BETWEEN 1 AND 100),
                description TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 100),
                category_id INTEGER NOT NULL
                    REFERENCES categories(id) ON DELETE RESTRICT,
                description TEXT,
                quantity_total INTEGER NOT NULL CHECK (quantity_total >= 1),
                quantity_available INTEGER NOT NULL,
                CHECK (quantity_available >= 0
                       AND quantity_available <= quantity_total)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS borrowers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL
                    CHECK (length(full_name) BETWEEN 1 AND 100),
                borrower_type TEXT NOT NULL
                    CHECK (borrower_type IN ('student', 'faculty')),
                id_number TEXT NOT NULL UNIQUE COLLATE NOCASE
                    CHECK (length(id_number) BETWEEN 1 AND 30),
                contact TEXT
            )
            """
        )