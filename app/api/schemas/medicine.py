import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MedicineBase(BaseModel):
    medicine_code: str = Field(..., min_length=2, max_length=50, description="Unique SKU or Barcode")
    name: str = Field(..., min_length=2, max_length=150, description="Trade / Brand name")
    generic_name: Optional[str] = Field(None, max_length=150, description="Active chemical / generic compound")
    category_id: uuid.UUID = Field(..., description="ID of the parent Category")
    manufacturer: Optional[str] = Field(None, max_length=150, description="Manufacturer company")
    unit_of_measurement: str = Field("Tablets", max_length=30, description="Dispensing unit (e.g. Tablets, Syrup, Strip)")
    reorder_level: int = Field(10, ge=0, description="Low stock alert threshold")
    prescription_required: bool = Field(False, description="Whether doctor prescription is legally required")
    is_active: bool = Field(True, description="Active status")


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    medicine_code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    generic_name: Optional[str] = Field(None, max_length=150)
    category_id: Optional[uuid.UUID] = None
    manufacturer: Optional[str] = Field(None, max_length=150)
    unit_of_measurement: Optional[str] = Field(None, max_length=30)
    reorder_level: Optional[int] = Field(None, ge=0)
    prescription_required: Optional[bool] = None
    is_active: Optional[bool] = None


class MedicineResponse(MedicineBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None
    total_stock: int = 0
    active_batches_count: int = 0

    model_config = ConfigDict(from_attributes=True)
