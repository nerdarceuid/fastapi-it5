"""Business logic for borrowing and returning equipment."""
import datetime
import sqlite3
from abc import ABC, abstractmethod
from app.exceptions import ConflictError
from app.models import DEFAULT_LOAN_DAYS
from app.repositories import BorrowerRepository, EquipmentRepository, LoanRepository

class PenaltyPolicy(ABC):
    @property # -> lets us read daily_rate
    @abstractmethod # -> every subclass must provide its own daily_rate
    def daily_rate(self) -> int:
        """Pesos charged for each late day."""

    def calculate(self, days_overdue: int) -> int:
        """The default rule: late days x daily rate

       never negative and returning early will cost nothing
        """
        return max(0, days_overdue) * self.daily_rate
 
 
class StudentPenaltyPolicy(PenaltyPolicy):
    """Students pay 10 pesos for every late day, starting the first day."""
 
    @property
    def daily_rate(self) -> int:
        return 10
 
 
class FacultyPenaltyPolicy(PenaltyPolicy):
    """Faculty get 2 grace days, then pay 5 pesos for every late day."""
 
    GRACE_DAYS = 2

    @property
    def daily_rate(self) -> int:
        return 5

    def calculate(self, days_overdue: int) -> int:
        return super().calculate(days_overdue - self.GRACE_DAYS)


# One ready-made policy object per borrower type. The keys are the same words
# stored in the borrowers table.
_PENALTY_POLICIES = {
    "student": StudentPenaltyPolicy(),
    "faculty": FacultyPenaltyPolicy(),
}


def get_penalty_policy(borrower_type: str) -> PenaltyPolicy:
    """Pick the right policy object for a borrower type ("student"/"faculty")."""
    return _PENALTY_POLICIES[borrower_type]


class LoanService:
    """Runs the borrow and return workflows on ONE open connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        # Three repositories built on the SAME connection = one shared
        # transaction (see the notes at the top of this file).
        self.borrowers = BorrowerRepository(connection)
        self.equipment = EquipmentRepository(connection)
        self.loans = LoanRepository(connection)

    def borrow(
        self,
        borrower_id: int,
        items: list[dict],
        due_date: datetime.date | None = None,
        notes: str | None = None,
        today: datetime.date | None = None,
    ) -> dict:
        """Borrow several equipment items in one all-or-nothing transaction.

        items looks like [{"equipment_id": 1, "quantity": 2}, ...].
        `today` exists only so tests can pretend it is another day.
        """
        today = today or datetime.date.today()

        # the borrower must exist (NotFoundError -> 404).
        self.borrowers.get(borrower_id)

        # (business rule): someone with a late, unreturned loan cannot
        # borrow again until it is returned (ConflictError -> 409).
        if self.loans.has_overdue(borrower_id, today):
            raise ConflictError(
                f"Borrower {borrower_id} has an overdue loan and must return "
                "it before borrowing again"
            )

        #  when no due date was given, use today + DEFAULT_LOAN_DAYS.
        # timedelta(days=7) is "a span of 7 days"; date + timedelta = a later date.
        due = due_date or today + datetime.timedelta(days=DEFAULT_LOAN_DAYS)

        # create the loan row. Dates are saved as ISO text.
        loan = self.loans.create(
            {
                "borrower_id": borrower_id,
                "borrowed_date": today.isoformat(),
                "due_date": due.isoformat(),
                "returned_date": None,
                "status": "active",
                "penalty_amount": 0,
                "notes": notes,
            }
        )

        for item in items:
            self.equipment.take_stock(item["equipment_id"], item["quantity"])
            self.loans.add_item(loan["id"], item["equipment_id"], item["quantity"])

        return self.loans.get_detail(loan["id"], today)

    def return_loan(self, loan_id: int, today: datetime.date | None = None) -> dict:
        """Return a loan: put the stock back and charge any late fee."""
        today = today or datetime.date.today()

        # The loan must exist (NotFoundError -> 404). This row includes the
        # borrower's type, which we need to choose the penalty policy.
        loan = self.loans.get(loan_id)

        # A loan can only be returned once (ConflictError -> 409).
        if loan["status"] == "returned":
            raise ConflictError(f"Loan {loan_id} was already returned")

        # Put every borrowed unit back on the shelf.
        for item in self.loans.get_items(loan_id):
            self.equipment.return_stock(item["equipment_id"], item["quantity"])

        # How many days late? A negative number (returned early) becomes 0
        # inside the policy's calculate().
        due = datetime.date.fromisoformat(loan["due_date"])
        days_late = (today - due).days

        policy = get_penalty_policy(loan["borrower_type"])
        penalty = policy.calculate(days_late)
 
        # Close the loan. update() changes only the three columns we pass.
        self.loans.update(
            loan_id,
            {
                "status": "returned",
                "returned_date": today.isoformat(),
                "penalty_amount": penalty,
            },
        )
        return self.loans.get_detail(loan_id, today)
