from typing import Annotated
from fastapi import APIRouter, Query, status
from app.database import database_connection
from app.models import Borrower, BorrowerInput, BorrowerType
from app.repositories import BorrowerRepository

router = APIRouter(prefix="/borrowers", tags=["borrowers"])

@router.post("", response_model=Borrower, status_code=status.HTTP_201_CREATED)
def create_borrower(borrower: BorrowerInput):
    with database_connection() as connection:
        return BorrowerRepository(connection).create(borrower.model_dump())
router.get("", response_model=list[Borrower])
def list_borrowers(

    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="Search text in the name or id number",
        ),
    ] = None,

    borrower_type: Annotated[
        BorrowerType | None, Query(description="Only students or only faculty")
    ] = None,
    skip: Annotated[int, Query(ge=0, description="How many records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum records to return")
    ] = 10,
):
    with database_connection() as connection:
        return BorrowerRepository(connection).search(
            q=q,
            borrower_type=borrower_type.value if borrower_type else None,
            skip=skip,
            limit=limit,
        )

@router.get("/{borrower_id}", response_model=Borrower)
def get_borrower(borrower_id: int):
    with database_connection() as connection:
        return BorrowerRepository(connection).get(borrower_id)

@router.put("/{borrower_id}", response_model=Borrower)
def update_borrower(borrower_id: int, borrower: BorrowerInput):
    with database_connection() as connection:
        return BorrowerRepository(connection).update(
            borrower_id, borrower.model_dump()
        )

@router.delete("/{borrower_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_borrower(borrower_id: int):
    with database_connection() as connection:
        BorrowerRepository(connection).delete(borrower_id)