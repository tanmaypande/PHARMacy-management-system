import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.billing_service import BillingService
from app.api.schemas.sale import (
    SaleCreate,
    SaleResponse,
    SalesSummaryResponse,
)

router = APIRouter(prefix="/api/v1/sales", tags=["Point of Sale & Dispensing"])


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process checkout and create bill",
    description="Validates batches, ensures zero-expiry compliance, deducts stock, and commits sale atomically."
)
def create_sale(sale_in: SaleCreate, db: Session = Depends(get_db)):
    try:
        sale = BillingService.create_sale(db, sale_in.model_dump())
        return sale
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while finalizing bill: {str(e)}"
        )


@router.get(
    "",
    response_model=List[SaleResponse],
    summary="List past bills and transactions",
    description="Returns past sales ordered by recent timestamp with optional search."
)
def list_sales(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by invoice number, customer name or phone"),
    db: Session = Depends(get_db)
):
    return BillingService.get_sales(db, limit=limit, offset=offset, search=search)


@router.get(
    "/summary/today",
    response_model=SalesSummaryResponse,
    summary="Get today's sales summary KPIs",
    description="Returns today's total revenue, bills count, and units dispensed."
)
def get_today_summary(db: Session = Depends(get_db)):
    return BillingService.get_today_summary(db)


@router.get(
    "/batches/available",
    summary="Get batches currently available for dispensing",
    description="Filters out quarantined, expired, or depleted batch lots."
)
def get_available_batches(
    medicine_id: Optional[uuid.UUID] = Query(None, description="Optional filter by medicine ID"),
    db: Session = Depends(get_db)
):
    return BillingService.get_available_batches_for_sale(db, medicine_id=medicine_id)


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get specific bill by ID",
    description="Returns complete invoice details including itemized lines."
)
def get_sale(sale_id: uuid.UUID, db: Session = Depends(get_db)):
    sale = BillingService.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with ID {sale_id} not found."
        )
    return sale


@router.get(
    "/invoice/{invoice_number}",
    response_model=SaleResponse,
    summary="Get bill by invoice number"
)
def get_sale_by_invoice(invoice_number: str, db: Session = Depends(get_db)):
    sale = BillingService.get_sale_by_invoice(db, invoice_number)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice '{invoice_number}' not found."
        )
    return sale
