import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.medicine import Medicine
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.category_repository import CategoryRepository
from app.api.schemas.medicine import MedicineCreate, MedicineUpdate, MedicineResponse


class MedicineService:
    def __init__(self, db: Session):
        self.repo = MedicineRepository(db)
        self.category_repo = CategoryRepository(db)

    def _to_response(self, medicine: Medicine) -> MedicineResponse:
        total_stock = sum(b.quantity for b in medicine.batches if b.is_active) if medicine.batches else 0
        active_batches = sum(1 for b in medicine.batches if b.is_active and b.quantity > 0) if medicine.batches else 0
        cat_name = medicine.category.name if medicine.category else None

        return MedicineResponse(
            id=medicine.id,
            medicine_code=medicine.medicine_code,
            name=medicine.name,
            generic_name=medicine.generic_name,
            category_id=medicine.category_id,
            category_name=cat_name,
            manufacturer=medicine.manufacturer,
            unit_of_measurement=medicine.unit_of_measurement,
            reorder_level=medicine.reorder_level,
            prescription_required=medicine.prescription_required,
            is_active=medicine.is_active,
            created_at=medicine.created_at,
            updated_at=medicine.updated_at,
            total_stock=total_stock,
            active_batches_count=active_batches
        )

    def get_medicine(self, medicine_id: uuid.UUID) -> MedicineResponse:
        med = self.repo.get_by_id(medicine_id)
        if not med:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine with ID '{medicine_id}' was not found"
            )
        return self._to_response(med)

    def list_medicines(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[MedicineResponse], int]:
        medicines, total = self.repo.list_all(
            skip=skip,
            limit=limit,
            search=search,
            category_id=category_id,
            is_active=is_active
        )
        return [self._to_response(m) for m in medicines], total

    def create_medicine(self, payload: MedicineCreate) -> MedicineResponse:
        # Check duplicate medicine code
        existing_code = self.repo.get_by_code(payload.medicine_code)
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A medicine with code '{payload.medicine_code}' already exists ({existing_code.name})"
            )

        # Validate category exists
        category = self.category_repo.get_by_id(payload.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with ID '{payload.category_id}' does not exist"
            )

        new_med = Medicine(
            medicine_code=payload.medicine_code.strip().upper(),
            name=payload.name.strip(),
            generic_name=payload.generic_name.strip() if payload.generic_name else None,
            category_id=payload.category_id,
            manufacturer=payload.manufacturer.strip() if payload.manufacturer else None,
            unit_of_measurement=payload.unit_of_measurement.strip(),
            reorder_level=payload.reorder_level,
            prescription_required=payload.prescription_required,
            is_active=payload.is_active
        )
        saved = self.repo.create(new_med)
        # Reload with joined category
        reloaded = self.repo.get_by_id(saved.id)
        return self._to_response(reloaded or saved)

    def update_medicine(self, medicine_id: uuid.UUID, payload: MedicineUpdate) -> MedicineResponse:
        med = self.repo.get_by_id(medicine_id)
        if not med:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine with ID '{medicine_id}' was not found"
            )

        # Code uniqueness check
        if payload.medicine_code and payload.medicine_code.strip().lower() != med.medicine_code.lower():
            existing = self.repo.get_by_code(payload.medicine_code)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Another medicine with code '{payload.medicine_code}' already exists"
                )

        # Category check
        if payload.category_id and payload.category_id != med.category_id:
            category = self.category_repo.get_by_id(payload.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target category with ID '{payload.category_id}' does not exist"
                )

        update_dict = payload.model_dump(exclude_unset=True)
        if "medicine_code" in update_dict and update_dict["medicine_code"]:
            update_dict["medicine_code"] = update_dict["medicine_code"].strip().upper()

        updated = self.repo.update(med, update_dict)
        return self._to_response(updated)

    def deactivate_medicine(self, medicine_id: uuid.UUID) -> MedicineResponse:
        """Soft delete: sets is_active = False so existing records maintain FK integrity."""
        med = self.repo.get_by_id(medicine_id)
        if not med:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine with ID '{medicine_id}' was not found"
            )
        updated = self.repo.update(med, {"is_active": False})
        return self._to_response(updated)
