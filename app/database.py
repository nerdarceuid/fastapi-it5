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
    #added pragma
    connection.execute("PRAGMA foreign_keys = ON")
    # SQLite ignores FOREIGN KEY rules unless this is switched on, and the
    # setting only lasts for ONE connection, so we set it every time we connect.
    # Without it, SQLite would let you add equipment for a category that does
    # not exist.

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the students table the first time the app runs."""

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



