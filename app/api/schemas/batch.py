import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BatchBase(BaseModel):
    medicine_id: uuid.UUID = Field(..., description="Referenced Medicine ID")
    supplier_id: Optional[uuid.UUID] = Field(None, description="Optional Supplier ID")
    batch_number: str = Field(..., min_length=2, max_length=50, description="Manufacturer batch / lot number")
    expiry_date: date = Field(..., description="Expiration date (YYYY-MM-DD)")
    cost_price: Decimal = Field(Decimal("0.00"), ge=0, description="Procurement cost price")
    selling_price: Decimal = Field(Decimal("0.00"), ge=0, description="Retail selling price")
    quantity: int = Field(..., ge=0, description="Available stock quantity")
    is_active: bool = Field(True, description="Active status")


class BatchCreate(BatchBase):
    pass


class BatchUpdate(BaseModel):
    supplier_id: Optional[uuid.UUID] = None
    expiry_date: Optional[date] = None
    cost_price: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class BatchResponse(BatchBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    medicine_name: Optional[str] = None
    medicine_code: Optional[str] = None
    supplier_name: Optional[str] = None
    is_expired: bool = False
    days_until_expiry: int = 0

    model_config = ConfigDict(from_attributes=True)
