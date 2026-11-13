"""
Database migration & Multi-Stakeholder Seeder for PostgreSQL.
Ensures new columns exist on legacy tables and seeds default multi-stakeholder accounts.
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import text
from app.core.database import engine, SessionLocal, Base
from app.models.pharmacy import Pharmacy, Subscription, Expense, SupportTicket
from app.models.role import Role, Permission, RolePermission
from app.models.user import User, AuditLog
from app.models.supplier import Supplier
from app.models.customer import Customer
from app.models.medicine import Medicine, Category
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.services.auth_service import hash_password


def run_migrations():
    """Add any missing columns to existing tables safely."""
    migration_statements = [
        # Users table extensions
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE SET NULL;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id) ON DELETE SET NULL;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(100);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(25);",
        "ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(30);",

        # Audit logs extensions
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE SET NULL;",

        # Domain tables tenant isolation
        "ALTER TABLE medicines ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE CASCADE;",
        "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE CASCADE;",
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE CASCADE;",
        "ALTER TABLE purchases ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE CASCADE;",
        "ALTER TABLE sales ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE CASCADE;",
        "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS pharmacy_id UUID REFERENCES pharmacies(id) ON DELETE CASCADE;",
        "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS prescription_number VARCHAR(50);",
        "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'Pending';",
        "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS verified_by VARCHAR(50);",
        "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS dispensing_notes TEXT;",
        "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;",
    ]

    with engine.begin() as conn:
        for stmt in migration_statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                # Column might already exist or table constraint already present
                pass


def seed_multi_stakeholder_data():
    """
    Seeds:
      1. Default Pharmacy (MediCare Central Pharmacy)
      2. Active Enterprise Subscription
      3. Standard RBAC Roles & Permissions
      4. Demo accounts for each of the 7 stakeholders
      5. Sample Purchase Order for cross-panel testing
      6. Sample Expenses & Support Tickets
    """
    with SessionLocal() as db:
        # 1. Default Pharmacy
        pharmacy = db.query(Pharmacy).first()
        if not pharmacy:
            pharmacy = Pharmacy(
                name="MediCare Central Pharmacy",
                license_number="DL-2026-MEDICARE-01",
                owner_name="Dr. Rajesh Varma",
                phone="+91 98765 43210",
                email="owner@medicare.com",
                address="Suite 104, Medical Square, Healthcare Blvd",
                status="active",
                subscription_plan="Enterprise"
            )
            db.add(pharmacy)
            db.flush()

            # Active Subscription
            now = datetime.now(timezone.utc)
            sub = Subscription(
                pharmacy_id=pharmacy.id,
                plan_name="Enterprise Platinum",
                status="active",
                price=Decimal("299.00"),
                billing_cycle="annual",
                start_date=now,
                end_date=now + timedelta(days=365)
            )
            db.add(sub)
            db.flush()

        # Update any null pharmacy_id on existing domain records
        try:
            db.execute(text(f"UPDATE medicines SET pharmacy_id = '{pharmacy.id}' WHERE pharmacy_id IS NULL"))
            db.execute(text(f"UPDATE suppliers SET pharmacy_id = '{pharmacy.id}' WHERE pharmacy_id IS NULL"))
            db.execute(text(f"UPDATE customers SET pharmacy_id = '{pharmacy.id}' WHERE pharmacy_id IS NULL"))
            db.execute(text(f"UPDATE purchases SET pharmacy_id = '{pharmacy.id}' WHERE pharmacy_id IS NULL"))
            db.execute(text(f"UPDATE sales SET pharmacy_id = '{pharmacy.id}' WHERE pharmacy_id IS NULL"))
            db.execute(text(f"UPDATE prescriptions SET pharmacy_id = '{pharmacy.id}' WHERE pharmacy_id IS NULL"))
            db.commit()
        except Exception:
            db.rollback()

        # 2. Seed Standard Roles
        roles_spec = [
            ("super_admin", "Super Administrator", "Software owner controlling platform, all pharmacies & licenses"),
            ("owner", "Pharmacy Owner", "Proprietor with full operational, financial & staffing control of pharmacy"),
            ("pharmacist", "Registered Pharmacist", "Clinical prescription review, dispensing verification & safety notes"),
            ("cashier", "Cashier / POS Executive", "Counter sales billing, payment collection, receipts & returns"),
            ("inventory_manager", "Inventory Manager", "Stock batch management, physical adjustments & purchase orders"),
            ("supplier", "Supplier / Distributor", "Wholesale vendor portal to confirm POs, quotations & delivery"),
            ("customer", "Patient / Customer", "Patient portal to browse catalog, upload Rx, view invoices & orders"),
        ]

        for role_name, disp_name, desc in roles_spec:
            existing_role = db.query(Role).filter(Role.name == role_name).first()
            if not existing_role:
                db.add(Role(name=role_name, display_name=disp_name, description=desc))
        db.commit()

        # 3. Seed demo accounts for each of the 7 stakeholders
        # Link supplier to an existing or demo supplier
        demo_supplier = db.query(Supplier).first()
        if not demo_supplier:
            demo_supplier = Supplier(
                name="Apex Pharma Distributors",
                contact_person="Ramesh Patel",
                phone="+91 91234 56789",
                email="supplier@apexpharma.com",
                address="Warehouse B, Logistics Park",
                pharmacy_id=pharmacy.id
            )
            db.add(demo_supplier)
            db.flush()

        # Link customer to an existing or demo customer
        demo_customer = db.query(Customer).first()
        if not demo_customer:
            demo_customer = Customer(
                name="Amit Sharma",
                phone="+91 99887 76655",
                email="patient.amit@gmail.com",
                address="12B Sunrise Apartments",
                pharmacy_id=pharmacy.id
            )
            db.add(demo_customer)
            db.flush()

        stakeholders_accounts = [
            {
                "username": "superadmin",
                "password": hash_password("super123"),
                "full_name": "Antigravity SuperAdmin",
                "role": "super_admin",
                "pharmacy_id": None,
                "email": "superadmin@antigravitypms.io",
                "phone": "+1 800 555 0199"
            },
            {
                "username": "owner",
                "password": hash_password("owner123"),
                "full_name": "Dr. Rajesh Varma (Proprietor)",
                "role": "owner",
                "pharmacy_id": pharmacy.id,
                "email": "owner@medicare.com",
                "phone": "+91 98765 43210"
            },
            {
                "username": "pharmacist",
                "password": hash_password("pharma123"),
                "full_name": "Pooja Deshmukh, M.Pharm",
                "role": "pharmacist",
                "pharmacy_id": pharmacy.id,
                "email": "pharmacist@medicare.com",
                "phone": "+91 98765 43211"
            },
            {
                "username": "cashier",
                "password": hash_password("cashier123"),
                "full_name": "Suresh Kumar (Cashier)",
                "role": "cashier",
                "pharmacy_id": pharmacy.id,
                "email": "cashier@medicare.com",
                "phone": "+91 98765 43212"
            },
            {
                "username": "inventory",
                "password": hash_password("stock123"),
                "full_name": "Vikram Singh (Inventory Lead)",
                "role": "inventory_manager",
                "pharmacy_id": pharmacy.id,
                "email": "inventory@medicare.com",
                "phone": "+91 98765 43213"
            },
            {
                "username": "supplier",
                "password": hash_password("vendor123"),
                "full_name": "Ramesh Patel (Apex Distributors)",
                "role": "supplier",
                "pharmacy_id": pharmacy.id,
                "supplier_id": demo_supplier.id,
                "email": "supplier@apexpharma.com",
                "phone": "+91 91234 56789"
            },
            {
                "username": "customer",
                "password": hash_password("patient123"),
                "full_name": "Amit Sharma (Patient)",
                "role": "customer",
                "pharmacy_id": pharmacy.id,
                "customer_id": demo_customer.id,
                "email": "patient.amit@gmail.com",
                "phone": "+91 99887 76655"
            },
        ]

        for acc in stakeholders_accounts:
            existing = db.query(User).filter(User.username == acc["username"]).first()
            if not existing:
                u = User(
                    username=acc["username"],
                    hashed_password=acc["password"],
                    full_name=acc["full_name"],
                    role=acc["role"],
                    pharmacy_id=acc.get("pharmacy_id"),
                    supplier_id=acc.get("supplier_id"),
                    customer_id=acc.get("customer_id"),
                    email=acc.get("email"),
                    phone=acc.get("phone"),
                    is_active=True
                )
                db.add(u)

        # 4. Sample Expenses
        sample_expenses = [
            ("Rent", Decimal("25000.00"), "Monthly dispensary premises rental"),
            ("Utilities", Decimal("4500.00"), "Electricity and refrigerated storage cooling bill"),
            ("Salaries", Decimal("85000.00"), "Staff payroll for current month"),
            ("Supplies", Decimal("3200.00"), "Dispensing envelopes, barcode thermal paper rolls"),
        ]
        if db.query(Expense).count() == 0:
            for cat, amt, desc in sample_expenses:
                exp = Expense(
                    pharmacy_id=pharmacy.id,
                    category=cat,
                    amount=amt,
                    description=desc,
                    recorded_by="owner"
                )
                db.add(exp)

        # 5. Sample Support Ticket
        if db.query(SupportTicket).count() == 0:
            ticket = SupportTicket(
                ticket_number="TCK-2026-001",
                pharmacy_id=pharmacy.id,
                sender_name="Dr. Rajesh Varma",
                sender_email="owner@medicare.com",
                subject="Request to increase user seats for weekend shifts",
                message="We are onboarding two part-time dispensing pharmacists for weekend shifts. Please verify seat allowance.",
                priority="Medium",
                status="Open"
            )
            db.add(ticket)

        db.commit()


def init_db_and_seed():
    """Entry point for full database setup and seeding."""
    Base.metadata.create_all(bind=engine)
    run_migrations()
    seed_multi_stakeholder_data()
