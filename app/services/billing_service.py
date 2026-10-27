import uuid
from datetime import datetime, timezone, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.models.sale import Sale, SaleItem
from app.models.batch import MedicineBatch
from app.models.medicine import Medicine
from app.models.customer import Customer


class BillingService:
    """
    Core Financial & Clinical Dispensation Service.
    Enforces TQM Safeguards:
    1. Zero Expired Dispensations: Rejects batches with expiry_date < today.
    2. Over-dispensation Protection: Validates available physical lot stock.
    3. Atomic Multi-Table Commit: Deducts stock and creates bill in one ACID transaction.
    4. Exact Decimal Arithmetic: Eliminates floating-point rounding errors.
    """

    @staticmethod
    def generate_invoice_number(db: Session) -> str:
        """
        Generates a clean sequential invoice number: INV-YYYYMMDD-XXXX
        """
        today_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix_pattern = f"INV-{today_prefix}-%"

        # Find maximum existing invoice number for today
        stmt = (
            select(Sale.invoice_number)
            .where(Sale.invoice_number.like(prefix_pattern))
            .order_by(desc(Sale.invoice_number))
            .limit(1)
        )
        last_invoice = db.execute(stmt).scalar_one_or_none()

        if last_invoice:
            try:
                last_seq = int(last_invoice.split("-")[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        return f"INV-{today_prefix}-{new_seq:04d}"

    @classmethod
    def create_sale(cls, db: Session, sale_data: Dict[str, Any]) -> Sale:
        """
        Creates an itemized sale transaction and deducts batch stock atomically.
        """
        raw_items = sale_data.get("items", [])
        if not raw_items:
            raise ValueError("Cannot create a bill with no medicine line items.")

        customer_name = (sale_data.get("customer_name") or "Walk-in Customer").strip()
        customer_phone = (sale_data.get("customer_phone") or "").strip() or None
        payment_method = sale_data.get("payment_method", "Cash")
        cashier_name = sale_data.get("cashier_name", "Pharmacist")
        notes = sale_data.get("notes")

        # Percentages
        discount_pct = Decimal(str(sale_data.get("discount_percent", 0) or 0))
        tax_pct = Decimal(str(sale_data.get("tax_percent", 0) or 0))

        if discount_pct < Decimal("0") or discount_pct > Decimal("100"):
            raise ValueError("Discount percentage must be between 0% and 100%.")
        if tax_pct < Decimal("0") or tax_pct > Decimal("100"):
            raise ValueError("Tax percentage must be between 0% and 100%.")

        today = date.today()
        sale_items_to_create = []
        running_subtotal = Decimal("0.00")

        # Step 1: Validate and process line items
        for item_data in raw_items:
            batch_id_raw = item_data.get("batch_id")
            if not batch_id_raw:
                raise ValueError("Missing batch identifier for line item.")

            try:
                batch_uuid = uuid.UUID(str(batch_id_raw))
            except ValueError:
                raise ValueError(f"Invalid UUID for batch: {batch_id_raw}")

            qty = int(item_data.get("quantity", 0))
            if qty <= 0:
                raise ValueError(f"Dispensing quantity must be at least 1 unit. Provided: {qty}")

            # Fetch batch with lock for update to prevent concurrent race conditions
            batch = (
                db.execute(
                    select(MedicineBatch)
                    .where(MedicineBatch.id == batch_uuid)
                    .with_for_update()
                )
                .scalar_one_or_none()
            )

            if not batch:
                raise ValueError(f"Inventory batch with ID {batch_uuid} does not exist.")

            # Load medicine
            medicine = db.execute(
                select(Medicine).where(Medicine.id == batch.medicine_id)
            ).scalar_one_or_none()

            med_name = medicine.name if medicine else "Unknown Pharmaceutical"
            med_code = medicine.medicine_code if medicine else "MED-UNKNOWN"

            # TQM Safeguard 1: Block Expired Lots
            if batch.expiry_date < today:
                raise ValueError(
                    f"CLINICAL SAFETY BLOCK: Batch '{batch.batch_number}' for '{med_name}' "
                    f"expired on {batch.expiry_date} and is quarantined from sale."
                )

            # TQM Safeguard 2: Physical Stock Availability
            if batch.quantity < qty:
                raise ValueError(
                    f"INSUFFICIENT STOCK: Product '{med_name}' (Batch: {batch.batch_number}) "
                    f"only has {batch.quantity} units available. Requested: {qty}."
                )

            # Determine Unit Price
            raw_unit_price = item_data.get("unit_price")
            if raw_unit_price is not None:
                unit_price = Decimal(str(raw_unit_price))
            else:
                unit_price = batch.selling_price

            if unit_price < Decimal("0"):
                raise ValueError("Unit price cannot be negative.")

            item_subtotal = (Decimal(qty) * unit_price).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            running_subtotal += item_subtotal

            # Deduct physical stock
            batch.quantity -= qty

            sale_items_to_create.append({
                "medicine_id": batch.medicine_id,
                "batch_id": batch.id,
                "medicine_name": med_name,
                "medicine_code": med_code,
                "batch_number": batch.batch_number,
                "expiry_date": batch.expiry_date,
                "unit_price": unit_price,
                "quantity": qty,
                "subtotal": item_subtotal,
            })

        # Step 2: Compute discounts, taxes, and grand total
        discount_amount = (running_subtotal * (discount_pct / Decimal("100"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        taxable_amount = max(Decimal("0.00"), running_subtotal - discount_amount)
        tax_amount = (taxable_amount * (tax_pct / Decimal("100"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        grand_total = (taxable_amount + tax_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        invoice_number = cls.generate_invoice_number(db)

        # Step 3: Handle optional Customer record linkage
        customer_id = None
        if sale_data.get("customer_id"):
            try:
                customer_id = uuid.UUID(str(sale_data["customer_id"]))
            except ValueError:
                customer_id = None

        new_sale = Sale(
            invoice_number=invoice_number,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            subtotal=running_subtotal,
            discount_percent=discount_pct,
            discount_amount=discount_amount,
            tax_percent=tax_pct,
            tax_amount=tax_amount,
            total_amount=grand_total,
            payment_method=payment_method,
            payment_status="Paid",
            cashier_name=cashier_name,
            notes=notes,
        )
        db.add(new_sale)
        db.flush()  # Generates new_sale.id

        # Attach line items
        for item_dict in sale_items_to_create:
            sale_item = SaleItem(
                sale_id=new_sale.id,
                medicine_id=item_dict["medicine_id"],
                batch_id=item_dict["batch_id"],
                medicine_name=item_dict["medicine_name"],
                medicine_code=item_dict["medicine_code"],
                batch_number=item_dict["batch_number"],
                expiry_date=item_dict["expiry_date"],
                unit_price=item_dict["unit_price"],
                quantity=item_dict["quantity"],
                subtotal=item_dict["subtotal"],
            )
            db.add(sale_item)

        db.commit()
        db.refresh(new_sale)
        return new_sale

    @staticmethod
    def get_sales(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Sale]:
        """
        Retrieves list of sales with optional search by invoice # or customer name.
        """
        stmt = (
            select(Sale)
            .options(joinedload(Sale.items))
            .order_by(desc(Sale.created_at))
        )

        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Sale.invoice_number.ilike(term),
                    Sale.customer_name.ilike(term),
                    Sale.customer_phone.ilike(term)
                )
            )

        stmt = stmt.limit(limit).offset(offset)
        result = db.execute(stmt).unique().scalars().all()
        return list(result)

    @staticmethod
    def get_sale_by_id(db: Session, sale_id: uuid.UUID) -> Optional[Sale]:
        """
        Fetches full sale by UUID with all itemized lines.
        """
        stmt = (
            select(Sale)
            .options(joinedload(Sale.items))
            .where(Sale.id == sale_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_sale_by_invoice(db: Session, invoice_number: str) -> Optional[Sale]:
        """
        Fetches sale by human-readable invoice number.
        """
        stmt = (
            select(Sale)
            .options(joinedload(Sale.items))
            .where(Sale.invoice_number == invoice_number.strip())
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_today_summary(db: Session) -> Dict[str, Any]:
        """
        Calculates daily summary: revenue, number of bills, and total units dispensed.
        """
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Revenue and count of sales today
        sales_stmt = select(
            func.coalesce(func.sum(Sale.total_amount), Decimal("0.00")),
            func.count(Sale.id)
        ).where(Sale.created_at >= today_start)

        rev, count_sales = db.execute(sales_stmt).one()

        # Units dispensed today
        items_stmt = select(
            func.coalesce(func.sum(SaleItem.quantity), 0)
        ).join(Sale, SaleItem.sale_id == Sale.id).where(Sale.created_at >= today_start)

        units_sold = db.execute(items_stmt).scalar() or 0

        return {
            "today_revenue": float(rev),
            "today_bills_count": int(count_sales),
            "today_units_dispensed": int(units_sold),
        }

    @staticmethod
    def get_available_batches_for_sale(
        db: Session,
        medicine_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns active, non-expired batches with stock > 0 ready for immediate dispensing.
        """
        today = date.today()
        stmt = (
            select(MedicineBatch, Medicine)
            .join(Medicine, MedicineBatch.medicine_id == Medicine.id)
            .where(
                MedicineBatch.is_active.is_(True),
                MedicineBatch.quantity > 0,
                MedicineBatch.expiry_date >= today
            )
            .order_by(Medicine.name, MedicineBatch.expiry_date)
        )

        if medicine_id:
            stmt = stmt.where(MedicineBatch.medicine_id == medicine_id)

        rows = db.execute(stmt).all()
        result = []
        for batch, med in rows:
            result.append({
                "batch_id": str(batch.id),
                "medicine_id": str(med.id),
                "medicine_name": med.name,
                "generic_name": med.generic_name or "",
                "medicine_code": med.medicine_code,
                "batch_number": batch.batch_number,
                "expiry_date": str(batch.expiry_date),
                "selling_price": float(batch.selling_price),
                "available_quantity": batch.quantity,
            })
        return result
