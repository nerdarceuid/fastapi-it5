"""
repository job is to talk to one table in the database. the rest of the application never writes SQL
just calling CategoryRepository(connection).create({...})
"""

import sqlite3
from app.exceptions import ConflictError, NotFoundError

class BaseRepository:

    table: str
    label: str
    columns: tuple[str, ...]

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
    
    #reading
    def list_all(self) -> list[dict]:

            rows = self.connection.execute(
                f"{self.select_sql} ORDER BY {self.id_column}"
            ).fetchall() #collects all matching rows into a list

            #then into dictionary
            return [dict(row) for row in rows]

    def find(self, row_id: int) -> dict| None:
        #basically returns a record or none if does not exists
        row = self.connection.execute(
            f"{self.select_sql} WHERE {self.id_column} = ?" (row_id,)
        ).fetchone()

        return dict(row) if row else None

    def get(self, row_id: int) -> dict:
        #returns the record or raise NotFoundError

        record = self.find(row_id)

        if record is None:
            raise NotFoundError(f"{self.label} {row_id} not found")
        
        return record

    #writing
    def create(self, data: dict) -> dict:
        columns = self._writable_columns(data)

        placeholders = ", ".join("?" for _ in columns)

        try:
            cursor = self.connection.execute(
            f"INSERT INTO {self.table} ({', '.join(columns)}) "
            f"VALUES ({placeholders})",
            # The values, in the SAME order as the columns.
            [data[column] for column in columns],
            )
        #checking if integrity error is violated
        except sqlite3.IntegrityError as error:
            raise self._conflict(error) from error
        
        return self.get(cursor.lastrowid)

    def update(self, row_id: int, data: dict) -> dict:
        columns = self._writable_columns(data)

        #depending on what assignments are called later
        assignments = ", ".join(f"{column} = ?" for column in columns)

        try:
            cursor = self.connection.execute(
                f"UPDATE {self.table} SET {assignments} WHERE id = ?",
                [data[column] for column in columns] + [row_id],
            )
        except sqlite3.IntegrityError as error:
            raise self._conflict(error) from error

        #if zero means no row -> nothing to update
        if cursor.rowcount == 0:
            raise NotFoundError(f"{self.label} {row_id} not found")
        return self.get(row_id)

    def delete(self, row_id: int) -> None:
        try:
            cursor = self.connection.execute(
            f"DELETE FROM {self.table} WHERE id = ?", (row_id,)
            )
        except sqlite3.IntegrityError as error:
            raise ConflictError(
                f"{self.label} {row_id} is still used by other records "
                "and cannot be deleted"
            ) from error

        if cursor.rowcount == 0:
            raise NotFoundError(f"{self.label} {row_id} not found")
        
    def _writable_columns(self, data: dict) -> list[str]:
        unknown = set(data) - set(self.columns)

        if unknown:
            raise ValueError(f"Unknown column(s) for {self.table}: {unknown}")
        return list(data)

    def _conflict(self, error: sqlite3.IntegrityError) -> ConflictError:
        #this RETURNS the error object; the caller does the `raise`.
        if "UNIQUE" in str(error):
            return ConflictError(f"A {self.label.lower()} with this name already exists")
        return ConflictError(f"{self.label} conflicts with existing data: {error}")

#baserepo + whatever I add
#basically it has all the crud with find, all it has to do is fill in
#the blanks
class CategoryRepository(BaseRepository):
    table = "categories"
    label = "Category"
    columns = ("name", "description")
    select_sql = "SELECT id, name, description FROM categories"

#same thing with this class
class EquipmentRepository(BaseRepository):
    table = "equipment"
    label = "Equipment"
    columns = (
        "name",
        "category_id",
        "description",
        "quantity_total",
        "quantity_available",
    )

    select_sql = (
        "SELECT e.id, e.name, e.category_id, c.name AS category_name, "
        "e.description, e.quantity_total, e.quantity_available "
        "FROM equipment AS e JOIN categories AS c ON c.id = e.category_id"
    )

    id_column = "e.id"

    def __init__(self, connection: sqlite3.Connection) -> None:
        super().__init__(connection)
        # equipment has a category, used to check that a category exists
        self.categories = CategoryRepository(connection)

            # OVERRIDING: this method has the same name as the parent's, so Python uses
    # THIS one for equipment. It adds rules, then calls the parent's version.

        def create(self, data: dict) -> dict:
            self.categories.get(data["category_id"])
            return super().create({**data, "quantity_available": data["quantity_total"]})

        def update(self, row_id: int, data: dict) -> dict:
            current = self.get(row_id)
            self.categories.get(data["category_id"])

        borrowed = current["quantity_total"] - current["quantity_available"]
        if data["quantity_total"] < borrowed:
            raise ConflictError(
                f"{borrowed} unit(s) are currently borrowed, so quantity_total "
                f"cannot be lower than {borrowed}"
            )
        return super().update(
            row_id,
            {**data, "quantity_available": data["quantity_total"] - borrowed},
        )
