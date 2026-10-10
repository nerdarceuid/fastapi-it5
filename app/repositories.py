import sqlite3
from app.exceptions import ConflictError, NotFoundError, InsufficientStockError

# this file covers a lot of OOP


class BaseRepository:
    """Shared CRUD logic. Subclasses only describe their own table."""

    table: str  
    label: str 
    columns: tuple[str, ...] 
    select_sql: str  

    id_column: str = "id"


    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_all(self) -> list[dict]:

        rows = self.connection.execute(
            f"{self.select_sql} ORDER BY {self.id_column}"
        ).fetchall()  

        return [dict(row) for row in rows]

    def find(self, row_id: int) -> dict | None:
        """Return the record, or None if it does not exist."""

        row = self.connection.execute(
            f"{self.select_sql} WHERE {self.id_column} = ?", (row_id,)
        ).fetchone() 

        return dict(row) if row else None

    def get(self, row_id: int) -> dict:
        """Return the record, or raise NotFoundError."""

        record = self.find(row_id)

        if record is None:

            raise NotFoundError(f"{self.label} {row_id} not found")
        return record

    # -- writing -------------------------------------------------------------
    def create(self, data: dict) -> dict:
        
        columns = self._writable_columns(data)

        placeholders = ", ".join("?" for _ in columns)

        try:
            
            cursor = self.connection.execute(
                f"INSERT INTO {self.table} ({', '.join(columns)}) "
                f"VALUES ({placeholders})",
    
                [data[column] for column in columns],
            )
        except sqlite3.IntegrityError as error:

            raise self._conflict(error) from error

        return self.get(cursor.lastrowid)

    def update(self, row_id: int, data: dict) -> dict:
        columns = self._writable_columns(data)

        assignments = ", ".join(f"{column} = ?" for column in columns)
        try:
            cursor = self.connection.execute(

                f"UPDATE {self.table} SET {assignments} WHERE id = ?",

                [data[column] for column in columns] + [row_id],
            )
        except sqlite3.IntegrityError as error:
            raise self._conflict(error) from error

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

    @staticmethod
    def _like_pattern(text: str) -> str:

        escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        return f"%{escaped}%"

    def _select_page(
        self, conditions: list[str], params: list, skip: int, limit: int
    ) -> list[dict]:
        """Run the table's SELECT with optional filters and paging.

        conditions: pieces of a WHERE clause, e.g. ["e.category_id = ?"]
        params:     the values for the ? placeholders in those conditions
        skip/limit: pagination (skip this many rows, return at most `limit`)
        """
        sql = self.select_sql

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += f" ORDER BY {self.id_column} LIMIT ? OFFSET ?"

        rows = self.connection.execute(sql, [*params, limit, skip]).fetchall()
        return [dict(row) for row in rows]

    def _conflict(self, error: sqlite3.IntegrityError) -> ConflictError:

        message = str(error)
        if "UNIQUE" in message:

            column = message.split(".")[-1].replace("_", " ")
            return ConflictError(
                f"A {self.label.lower()} with this {column} already exists"
            )
        return ConflictError(f"{self.label} conflicts with existing data: {error}")


class CategoryRepository(BaseRepository):
    table = "categories"
    label = "Category"
    columns = ("name", "description")
    select_sql = "SELECT id, name, description FROM categories"


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

        self.categories = CategoryRepository(connection)


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

    def search(
        self,
        q: str | None = None,
        category_id: int | None = None,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 10,
    ) -> list[dict]:

        conditions: list[str] = []
        params: list = []

        if q is not None:
            pattern = self._like_pattern(q)
            conditions.append(
                "(e.name LIKE ? ESCAPE '\\' OR e.description LIKE ? ESCAPE '\\')"
            )
            params += [pattern, pattern]

        if category_id is not None:
            conditions.append("e.category_id = ?")
            params.append(category_id)

        if available_only:
            conditions.append("e.quantity_available > 0")

        return self._select_page(conditions, params, skip, limit)

class BorrowerRepository(BaseRepository):
    table = "borrowers"
    label = "Borrower"
    columns = ("full_name", "borrower_type", "id_number", "contact")
    select_sql = (
        "SELECT id, full_name, borrower_type, id_number, contact FROM borrowers"
    )

    def search(
        self,
        q: str | None = None,
        borrower_type: str | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> list[dict]:
        conditions: list[str] = []
        params: list = []


        if q is not None:
            pattern = self._like_pattern(q)
            conditions.append(
                "(full_name LIKE ? ESCAPE '\\' OR id_number LIKE ? ESCAPE '\\')"
            )
            params += [pattern, pattern]

        # Only students, or only faculty.
        if borrower_type is not None:
            conditions.append("borrower_type = ?")
            params.append(borrower_type)

        return self._select_page(conditions, params, skip, limit)

class LoanRepository(BaseRepository):
    table = "loans"
    label = "Loan"
    columns = (
        "borrower_id",
        "borrowed_date",
        "due_date",
        "returned_date",
        "status",
        "penalty_amount",
        "notes",
    )

    select_sql = (
        "SELECT l.id, l.borrower_id, b.full_name AS borrower_name, "
        "b.borrower_type, l.borrowed_date, l.due_date, l.returned_date, "
        "l.status, l.penalty_amount, l.notes "
        "FROM loans AS l JOIN borrowers AS b ON b.id = l.borrower_id"
    )
    id_column = "l.id"

    def has_overdue(self, borrower_id: int, today: datetime.date) -> bool:
        """True if this borrower has an active loan whose due date has passed."""
        # ISO date text can be compared with < and > like normal dates.
        row = self.connection.execute(
            "SELECT EXISTS (SELECT 1 FROM loans WHERE borrower_id = ? "
            "AND status = 'active' AND due_date < ?)",
            (borrower_id, today.isoformat()),
        ).fetchone()
        return bool(row[0])
 
    def add_item(self, loan_id: int, equipment_id: int, quantity: int) -> None:
        try:
            self.connection.execute(
                "INSERT INTO loan_items (loan_id, equipment_id, quantity) "
                "VALUES (?, ?, ?)",
                (loan_id, equipment_id, quantity),
            )
        except sqlite3.IntegrityError as error:
            raise self._conflict(error) from error
 
    def get_items(self, loan_id: int) -> list[dict]:
        # JOIN equipment so each item line also shows the equipment's name.
        rows = self.connection.execute(
            "SELECT li.equipment_id, e.name AS equipment_name, li.quantity "
            "FROM loan_items AS li JOIN equipment AS e ON e.id = li.equipment_id "
            "WHERE li.loan_id = ? ORDER BY li.id",
            (loan_id,),
        ).fetchall()
        return [dict(row) for row in rows]
 
    def present(self, loan: dict, today: datetime.date | None = None) -> dict:
        """Turn a stored loan row into what the API shows.
 
        Adds the item lines, works out days_overdue, and replaces the stored
        status 'active' with 'overdue' when the due date has passed.
        """
        # `today or datetime.date.today()` = use the given date, else the real one.
        today = today or datetime.date.today()
        # fromisoformat turns the stored text "2026-10-11" back into a date.
        due = datetime.date.fromisoformat(loan["due_date"])
 
        if loan["status"] == "returned":
            returned = datetime.date.fromisoformat(loan["returned_date"])
            status = "returned"
            # max(0, ...) so an early return never gives a negative number.
            days_overdue = max(0, (returned - due).days)
        else:
            days_overdue = max(0, (today - due).days)
            status = "overdue" if days_overdue > 0 else "active"
 
        # {**loan, ...} copies the row and replaces/adds the listed keys.
        return {
            **loan,
            "status": status,
            "days_overdue": days_overdue,
            "items": self.get_items(loan["id"]),
        }
 
    def get_detail(self, loan_id: int, today: datetime.date | None = None) -> dict:
        # get() raises NotFoundError (-> 404) when the loan does not exist.
        return self.present(self.get(loan_id), today)
 
    def search(
        self,
        q: str | None = None,
        borrower_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 10,
        today: datetime.date | None = None,
    ) -> list[dict]:
        today = today or datetime.date.today()
        conditions: list[str] = []
        params: list = []
 
        # Text search in the borrower's name or id number (both come from the
        # JOINed borrowers table, which has the nickname b).
        if q is not None:
            pattern = self._like_pattern(q)
            conditions.append(
                "(b.full_name LIKE ? ESCAPE '\\' OR b.id_number LIKE ? ESCAPE '\\')"
            )
            params += [pattern, pattern]
 
        # Only the loans of one borrower.
        if borrower_id is not None:
            conditions.append("l.borrower_id = ?")
            params.append(borrower_id)
 
        # The status filter. "overdue" and "active" are not stored, so we build
        # them from the stored status plus the due date.
        if status == "returned":
            conditions.append("l.status = 'returned'")
        elif status == "active":
            conditions.append("l.status = 'active' AND l.due_date >= ?")
            params.append(today.isoformat())
        elif status == "overdue":
            conditions.append("l.status = 'active' AND l.due_date < ?")
            params.append(today.isoformat())
 
        rows = self._select_page(conditions, params, skip, limit)
        # Add items / days_overdue / the real status to each loan.
        return [self.present(row, today) for row in rows]
