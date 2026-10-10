from typing import Annotated
from fastapi import APIRouter, Query, status
from app.database import database_connection
from app.models import Equipment, EquipmentInput
from app.repositories import EquipmentRepository

router = APIRouter(prefix="/equipment", tags=["equipment"])

@router.post("", response_model=Equipment, status_code=status.HTTP_201_CREATED)
def create_equipment(equipment: EquipmentInput):
    with database_connection() as connection:
        # model_dump() turns the validated object into a plain dictionary.
        return EquipmentRepository(connection).create(equipment.model_dump())


@router.get("", response_model=list[Equipment])
def list_equipment(
    
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="Search text in the name or description",
        ),
    ] = None,
    
    category_id: Annotated[
        int | None, Query(ge=1, description="Only equipment of this category")
    ] = None,
   
    available_only: Annotated[
        bool, Query(description="Only equipment with units available")
    ] = False,
   

    skip: Annotated[int, Query(ge=0, description="How many records to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum records to return")
    ] = 10,
):
    with database_connection() as connection:

        return EquipmentRepository(connection).search(
            q=q,
            category_id=category_id,
            available_only=available_only,
            skip=skip,
            limit=limit,
        )

@router.get("/{equipment_id}", response_model=Equipment)
def get_equipment(equipment_id: int):
    with database_connection() as connection:
        return EquipmentRepository(connection).get(equipment_id)

@router.put("/{equipment_id}", response_model=Equipment)
def update_equipment(equipment_id: int, equipment: EquipmentInput):
    with database_connection() as connection:
        return EquipmentRepository(connection).update(
            equipment_id, equipment.model_dump()
        )

@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int):
    with database_connection() as connection:
        EquipmentRepository(connection).delete(equipment_id)