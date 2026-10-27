import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class SaleItemCreate(BaseModel):
    batch_id: uuid.UUID = Field(..., description="ID of inventory batch being dispensed")
    quantity: int = Field(..., ge=1, description="Quantity of units to dispense")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Override unit price; defaults to batch retail price")


class SaleCreate(BaseModel):
    customer_id: Optional[uuid.UUID] = Field(None, description="Optional registered customer UUID")
    customer_name: str = Field("Walk-in Customer", max_length=150, description="Customer or patient name")
    customer_phone: Optional[str] = Field(None, max_length=50, description="Customer contact phone")
    payment_method: str = Field("Cash", description="Payment method: Cash, Credit Card, Debit Card, UPI, etc.")
    discount_percent: Decimal = Field(Decimal("0.00"), ge=0, le=100, description="Discount percentage")
    tax_percent: Decimal = Field(Decimal("0.00"), ge=0, le=100, description="Tax/GST percentage")
    cashier_name: str = Field("Pharmacist", max_length=100, description="Name of dispensing staff member")
    notes: Optional[str] = Field(None, description="Prescription or transaction notes")
    items: List[SaleItemCreate] = Field(..., min_length=1, description="Prescription dispensation line items")


class SaleItemResponse(BaseModel):
    id: uuid.UUID
    medicine_id: uuid.UUID
    batch_id: uuid.UUID
    medicine_name: str
    medicine_code: str
    batch_number: str
    expiry_date: date
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SaleResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    customer_id: Optional[uuid.UUID] = None
    customer_name: str
    customer_phone: Optional[str] = None
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    tax_percent: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_method: str
    payment_status: str
    cashier_name: str
    notes: Optional[str] = None
    created_at: datetime
    items: List[SaleItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SalesSummaryResponse(BaseModel):
    today_revenue: float
    today_bills_count: int
    today_units_dispensed: int
