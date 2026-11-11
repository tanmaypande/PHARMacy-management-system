import os
import csv
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from app.models.sale import Sale, SaleItem
from app.models.batch import MedicineBatch
from app.models.medicine import Medicine
from app.models.purchase import Purchase


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_sales_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculates revenue, gross profit, sales count, and day-by-day trend.
        """
        since_date = datetime.now(timezone.utc) - timedelta(days=days)

        sales_stmt = (
            select(Sale)
            .where(Sale.created_at >= since_date, Sale.payment_status == "Paid")
            .order_by(Sale.created_at.asc())
        )
        sales = list(self.db.scalars(sales_stmt).all())

        total_rev = Decimal("0.00")
        total_profit = Decimal("0.00")
        day_buckets: Dict[str, float] = {}

        for s in sales:
            total_rev += s.total_amount
            day_str = s.created_at.strftime("%Y-%m-%d")
            day_buckets[day_str] = day_buckets.get(day_str, 0.0) + float(s.total_amount)

            # Profit estimate: selling price - batch cost price
            for item in s.items:
                cost = item.batch.cost_price if item.batch else Decimal("0.00")
                profit_per_unit = item.unit_price - cost
                total_profit += profit_per_unit * Decimal(item.quantity)

        return {
            "period_days": days,
            "total_sales_count": len(sales),
            "total_revenue": float(total_rev),
            "total_profit": float(total_profit),
            "daily_trend": [{"date": k, "amount": v} for k, v in sorted(day_buckets.items())]
        }

    def get_inventory_valuation(self) -> Dict[str, Any]:
        batches = list(self.db.scalars(select(MedicineBatch).where(MedicineBatch.is_active.is_(True))).all())
        total_items = len(batches)
        total_cost_val = sum(float(b.cost_price) * b.quantity for b in batches)
        total_retail_val = sum(float(b.selling_price) * b.quantity for b in batches)
        total_units = sum(b.quantity for b in batches)

        return {
            "total_batches": total_items,
            "total_units": total_units,
            "total_cost_value": total_cost_val,
            "total_retail_value": total_retail_val,
            "potential_margin": total_retail_val - total_cost_val
        }

    def export_sales_csv(self, file_path: str, days: int = 30) -> str:
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        sales = list(self.db.scalars(select(Sale).where(Sale.created_at >= since_date).order_by(desc(Sale.created_at))).all())

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Invoice Number", "Date", "Customer", "Subtotal", "Discount", "Tax", "Total Amount", "Payment Method", "Status"])
            for s in sales:
                writer.writerow([
                    s.invoice_number,
                    s.created_at.strftime("%Y-%m-%d %H:%M"),
                    s.customer_name,
                    float(s.subtotal),
                    float(s.discount_amount),
                    float(s.tax_amount),
                    float(s.total_amount),
                    s.payment_method,
                    s.payment_status
                ])
        return file_path
