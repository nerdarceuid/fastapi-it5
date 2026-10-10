from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from enum import Enum
import datetime

class CategoryInput(BaseModel):

    #extra="forbid" used if the users sends a field thats type or random then returns 422
    # the other one is self explanatory
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)

    description: str | None = Field(default=None, max_length=500)

#inherits categoryInput, this one will be sent back to the users
#Basically category as returned by the api
class Category(CategoryInput):

    #plain int, no rules. No clients should be able to send this field
    id: int

class EquipmentInput(BaseModel):
    """
    fields a user sends when for creating and updating

    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)

    category_id: int = Field(ge=1)

    description: str | None = Field(default=None, max_length=500)
    #preventing 999999999999 typo related
    quantity_total: int = Field(ge=1, le=10000)

class Equipment(EquipmentInput):

    id: int
    category_name: str
    quantity_available: int

class BorrowerType(str, Enum):
    student = "student"
    faculty = "faculty"

class BorrowerInput(BaseModel):
    """Fields a client sends when creating or replacing a borrower."""
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, use_enum_values=True
    )

    full_name: str = Field(min_length=1, max_length=100)
    borrower_type: BorrowerType
    id_number: str = Field(min_length=1, max_length=30)
    contact: str | None = Field(default=None, max_length=100)

class Borrower(BorrowerInput):
    """A borrower as returned by the API."""
    id: int

#Loan rules
DEFAULT_LOAN_DAYS = 7
MAX_LOAN_DAYS = 14

class LoanStatus(str, Enum):

    #the states of loan
    active = "active"
    overdue = "overdue"
    returned = "returned"

class LoanItemInput(BaseModel):

    model_config = ConfigDict(extra="forbid")
    equipment_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=100)

class LoanInput(BaseModel):
    #body of POST /loans

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples" : [
                {
                    "borrower_id": 1,
                    "items": [{"equipment_id": 1, "quantity": 2}],
                    "notes": "For my programming references"
                }
            ]
        },
    )

    borrow_id: int = Field(ge=1)

    #if the clients leaves it out, the service uses today + 7 days
    due_date: datetime.date | None = None

    #list of items then should be at least one and stops at 10 max length because its already absurdly long
    items: list[LoanItemInput] = Field(min_length=1, max_length=20)

    notes: str | None = Field(default=None, max_length=500)

    #Importan rule -> due date must be today or later, and no more than max loan days (var above)
    # it will raise value error (422)

    @field_validator("due_date")
    @classmethod
    def due_date_in_allowed_range(
        cls, value: datetime.date | None
    ) -> datetime.date | None:
        if value is None:
            return value
        today = datetime.date.today()
        if value < today:
            raise ValueError("due_date cannot be in the past")
        if value > today + datetime.timedelta(days=MAX_LOAN_DAYS):
            raise ValueError(
                f"due_date cannot be more than {MAX_LOAN_DAYS} days from today"
            )
        return value

    # Another important rule -> the same equipment may appear only once per request. This validator
    # runs AFTER every field has been checked individually (mode="after") so it
    # can look at the whole list
    @model_validator(mode="after")
    def equipment_must_be_unique(self) -> "LoanInput":
        ids = [item.equipment_id for item in self.items]
        # A set removes duplicates, so a shorter set means a repeated id.
        if len(ids) != len(set(ids)):
            raise ValueError("each equipment may appear only once per loan")
        return self
class LoanItem(BaseModel):

    equipment_id: int
    equipment_name: str
    quantity: int

class Loan(BaseModel):

    id: int
    borrower_id: int
    borrower_name: str
    borrower_type: BorrowerType
    borrowed_date: datetime.date
    due_date: datetime.date
    returned_date: datetime.date | None
    status: LoanStatus
    # How many days late. For an active loan: days past the due date so far.
    # For a returned loan: days between the due date and the return date.
    days_overdue: int
    # The late fee in pesos (0 until the loan is returned late).
    penalty_amount: int
    notes: str | None
    items: list[LoanItem]
