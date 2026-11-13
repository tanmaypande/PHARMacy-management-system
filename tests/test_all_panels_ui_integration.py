"""
Test Suite: Multi-Stakeholder UI Integration & Panel Verification.
Verifies MainWindow lifecycle, dynamic stakeholder navigation,
and rendering for all 7 panels without exceptions.
"""
import os
import sys
import pathlib
import pytest

# Ensure TCL and TK libraries are properly located on Windows
base_prefix = pathlib.Path(sys.base_prefix)
tcl_dir = base_prefix / "tcl" / "tcl8.6"
tk_dir = base_prefix / "tcl" / "tk8.6"
if tcl_dir.exists() and "TCL_LIBRARY" not in os.environ:
    os.environ["TCL_LIBRARY"] = str(tcl_dir)
if tk_dir.exists() and "TK_LIBRARY" not in os.environ:
    os.environ["TK_LIBRARY"] = str(tk_dir)

from app.core.db_migration import init_db_and_seed
from app.ui.main_window import MainWindow
from app.ui.auth.login_view import LoginView
from app.ui.super_admin.super_admin_view import SuperAdminView
from app.ui.owner.owner_view import OwnerView
from app.ui.pharmacist.pharmacist_view import PharmacistView
from app.ui.cashier.cashier_view import CashierView
from app.ui.inventory_manager.inventory_manager_view import InventoryManagerView
from app.ui.supplier.supplier_portal_view import SupplierPortalView
from app.ui.customer.customer_portal_view import CustomerPortalView


@pytest.fixture(scope="module")
def app_instance():
    init_db_and_seed()
    app = MainWindow()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def test_mainwindow_unauthenticated_shows_login(app_instance):
    """Verify MainWindow starts on LoginView when unauthenticated."""
    app_instance.update_idletasks()
    assert isinstance(app_instance.current_view_widget, LoginView)
    assert not bool(app_instance.sidebar.grid_info())  # Sidebar removed from grid


def test_mainwindow_super_admin_panel(app_instance):
    """Verify login and navigation for Super Admin Panel."""
    demo_user = {
        "id": 1,
        "username": "superadmin",
        "full_name": "Global Super Administrator",
        "role": "super_admin",
        "email": "superadmin@medicare.global"
    }
    app_instance._on_login_success(demo_user)
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, SuperAdminView)
    assert bool(app_instance.sidebar.grid_info())  # Sidebar active in grid
    assert "super_admin" in app_instance.nav_buttons
    assert "users" in app_instance.nav_buttons
    assert "settings" in app_instance.nav_buttons

    # Switch to settings and back
    app_instance.navigate("settings")
    app_instance.update_idletasks()
    assert app_instance.current_view_key == "settings"

    app_instance.navigate("super_admin")
    app_instance.update_idletasks()
    assert isinstance(app_instance.current_view_widget, SuperAdminView)


def test_mainwindow_owner_panel(app_instance):
    """Verify login and navigation for Pharmacy Owner Panel."""
    demo_user = {
        "id": 2,
        "username": "owner",
        "full_name": "Pharmacy Managing Director",
        "role": "owner",
        "email": "owner@medicare.com"
    }
    app_instance._on_login_success(demo_user)
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, OwnerView)
    assert "owner" in app_instance.nav_buttons
    assert "dashboard" in app_instance.nav_buttons
    assert "medicines" in app_instance.nav_buttons
    assert "sales" in app_instance.nav_buttons

    app_instance.navigate("medicines")
    app_instance.update_idletasks()
    assert app_instance.current_view_key == "medicines"

    app_instance.navigate("owner")
    app_instance.update_idletasks()
    assert isinstance(app_instance.current_view_widget, OwnerView)


def test_mainwindow_pharmacist_panel(app_instance):
    """Verify login and navigation for Pharmacist Clinical Panel."""
    demo_user = {
        "id": 3,
        "username": "pharmacist",
        "full_name": "Dr. Sarah Pharmacist, PharmD",
        "role": "pharmacist",
        "email": "pharmacist@medicare.com"
    }
    app_instance._on_login_success(demo_user)
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, PharmacistView)
    assert "pharmacist" in app_instance.nav_buttons
    assert "prescriptions" in app_instance.nav_buttons
    assert "medicines" in app_instance.nav_buttons


def test_mainwindow_cashier_panel(app_instance):
    """Verify login and navigation for Cashier / POS Panel."""
    demo_user = {
        "id": 4,
        "username": "cashier",
        "full_name": "Front Desk Billing Officer",
        "role": "cashier",
        "email": "cashier@medicare.com"
    }
    app_instance._on_login_success(demo_user)
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, CashierView)
    assert "cashier" in app_instance.nav_buttons
    assert "sales" in app_instance.nav_buttons


def test_mainwindow_inventory_manager_panel(app_instance):
    """Verify login and navigation for Inventory Manager Panel."""
    demo_user = {
        "id": 5,
        "username": "inventory",
        "full_name": "Supply Chain & Warehouse Lead",
        "role": "inventory_manager",
        "email": "inventory@medicare.com"
    }
    app_instance._on_login_success(demo_user)
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, InventoryManagerView)
    assert "inventory_manager" in app_instance.nav_buttons
    assert "inventory" in app_instance.nav_buttons
    assert "suppliers" in app_instance.nav_buttons


def test_mainwindow_supplier_panel(app_instance):
    """Verify login and navigation for Supplier Portal Panel."""
    demo_user = {
        "id": 6,
        "username": "supplier",
        "full_name": "Apex Pharma Logistics",
        "role": "supplier",
        "email": "orders@apexpharma.com"
    }
    app_instance._on_login_success(demo_user)
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, SupplierPortalView)
    assert "supplier" in app_instance.nav_buttons


def test_mainwindow_customer_panel(app_instance):
    """Verify login and navigation for Patient & Customer Portal Panel."""
    demo_user = {
        "id": 7,
        "username": "customer",
        "full_name": "John Doe Patient",
        "role": "customer",
        "email": "john.doe@gmail.com"
    }
    app_instance._on_login_success(demo_user)
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, CustomerPortalView)
    assert "customer" in app_instance.nav_buttons


def test_mainwindow_logout(app_instance):
    """Verify logout returns cleanly to LoginView and hides sidebar."""
    app_instance._handle_logout()
    app_instance.update_idletasks()

    assert isinstance(app_instance.current_view_widget, LoginView)
    assert not bool(app_instance.sidebar.grid_info())
