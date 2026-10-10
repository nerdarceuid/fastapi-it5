from fastapi import APIRouter, status
from app.database import database_connection
from app.models import Category, CategoryInput
from app.repositories import CategoryRepository

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryInput):
    with database_connection() as connection:
        return CategoryRepository(connection).create(category.model_dump())

@router.get("", response_model=list[Category])
def list_categories():
    with database_connection() as connection:
        return CategoryRepository(connection).list_all()

@router.get("/{category_id}", response_model=Category)
def get_category(category_id: int):
    with database_connection() as connection:
        return CategoryRepository(connection).get(category_id)

@router.put("/{category_id}", response_model=Category)
def update_category(category_id: int, category: CategoryInput):
    with database_connection() as connection:
        return CategoryRepository(connection).update(category_id, category.model_dump())

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int):
    with database_connection() as connection:
        CategoryRepository(connection).delete(category_id)
