import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.medicine import Category
from app.repositories.category_repository import CategoryRepository
from app.api.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse


class CategoryService:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def get_category(self, category_id: uuid.UUID) -> CategoryResponse:
        category = self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' was not found"
            )
        count = self.repo.count_medicines(category.id)
        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            created_at=category.created_at,
            medicine_count=count
        )

    def list_categories(self, skip: int = 0, limit: int = 100) -> List[CategoryResponse]:
        categories = self.repo.list_all(skip=skip, limit=limit)
        results = []
        for cat in categories:
            count = self.repo.count_medicines(cat.id)
            results.append(
                CategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    description=cat.description,
                    created_at=cat.created_at,
                    medicine_count=count
                )
            )
        return results

    def create_category(self, payload: CategoryCreate) -> CategoryResponse:
        # Check duplicate name
        existing = self.repo.get_by_name(payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A category named '{payload.name}' already exists"
            )

        new_cat = Category(
            name=payload.name.strip(),
            description=payload.description.strip() if payload.description else None
        )
        saved = self.repo.create(new_cat)
        return CategoryResponse(
            id=saved.id,
            name=saved.name,
            description=saved.description,
            created_at=saved.created_at,
            medicine_count=0
        )

    def update_category(self, category_id: uuid.UUID, payload: CategoryUpdate) -> CategoryResponse:
        category = self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' was not found"
            )

        if payload.name and payload.name.strip().lower() != category.name.lower():
            existing = self.repo.get_by_name(payload.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Another category named '{payload.name}' already exists"
                )

        update_data = {}
        if payload.name is not None:
            update_data["name"] = payload.name.strip()
        if payload.description is not None:
            update_data["description"] = payload.description.strip()

        updated = self.repo.update(category, update_data)
        count = self.repo.count_medicines(updated.id)
        return CategoryResponse(
            id=updated.id,
            name=updated.name,
            description=updated.description,
            created_at=updated.created_at,
            medicine_count=count
        )

    def delete_category(self, category_id: uuid.UUID) -> None:
        category = self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID '{category_id}' was not found"
            )

        medicine_count = self.repo.count_medicines(category_id)
        if medicine_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category '{category.name}' because it contains {medicine_count} registered medicine(s). Reassign or delete the medicines first."
            )

        self.repo.delete(category)
