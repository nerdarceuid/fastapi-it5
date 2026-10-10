from typing import Annotated
# APIRouter groups endpoints; Query describes URL query parameters; status holds
# the named HTTP status codes.
from fastapi import APIRouter, Query, status
from app.database import database_connection
from app.models import Loan, LoanInput, LoanStatus
from app.repositories import LoanRepository
from app.services import LoanService


router = APIRouter(prefix="/loans", tags=["loans"])

@router.post("", response_model=Loan, status_code=status.HTTP_201_CREATED)
def borrow_equipment(loan: LoanInput):
    with database_connection() as connection:
        return LoanService(connection).borrow(
            borrower_id=loan.borrower_id,
            # Each LoanItemInput object becomes a plain dictionary.
            items=[item.model_dump() for item in loan.items],
            due_date=loan.due_date,
            notes=loan.notes,
        )

@router.get("", response_model=list[Loan])
def list_loans(
    # Search text: matches the borrower's name or id number.
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="Search text in the borrower's name or id number",
        ),
    ] = None,

    borrower_id: Annotated[
        int | None, Query(ge=1, description="Only loans of this borrower")
    ] = None,

    status_filter: Annotated[
        LoanStatus | None,
        Query(alias="status", description="active, overdue or returned"),
    ] = None,
    skip: Annotated[int, Query(ge=0, description="How many records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum records to return")
    ] = 10,
):
    with database_connection() as connection:
        return LoanRepository(connection).search(
            q=q,
            borrower_id=borrower_id,
            # The enum member becomes its plain text value ("overdue").
            status=status_filter.value if status_filter else None,
            skip=skip,
            limit=limit,
        )

@router.get("/{loan_id}", response_model=Loan)
def get_loan(loan_id: int):
    with database_connection() as connection:
        return LoanRepository(connection).get_detail(loan_id)

@router.post("/{loan_id}/return", response_model=Loan)
def return_loan(loan_id: int):
    with database_connection() as connection:
        return LoanService(connection).return_loan(loan_id)
