import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.ui.components.stat_card import StatCard
from app.ui.components.data_table import DataTable
from app.client.api_client import APIClient


class SupplierPortalView(ctk.CTkFrame):
    """
    Panel 6: Supplier / Wholesale Distributor Panel
    Allows distributors to interact with pharmacies:
    View assigned wholesale purchase orders, accept/reject with quotation notes,
    track fulfillment status, view supplied catalog, and inspect payment ledger.
    """
    def __init__(self, parent, api_client: APIClient):
        super().__init__(parent, fg_color=Theme.BG_APP)
        self.api_client = api_client

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header Banner
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        ctk.CTkLabel(
            header,
            text="🚚 Wholesale Distributor & Supplier Portal",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="↻ Refresh Orders",
            width=110,
            font=accessibility_manager.get_font(12),
            fg_color=Theme.BG_MUTED,
            text_color=Theme.TEXT_MAIN,
            command=self.load_data
        ).pack(side="right")

        # 2. KPI Cards
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        for col in range(4):
            self.kpi_frame.grid_columnconfigure(col, weight=1)

        self.card_orders = StatCard(self.kpi_frame, title="Assigned Orders", value="0", subtitle="Total POs issued", icon="📋")
        self.card_orders.grid(row=0, column=0, sticky="nsew", padx=6)

        self.card_pending = StatCard(self.kpi_frame, title="Awaiting Acceptance", value="0", subtitle="Action required", icon="⏳")
        self.card_pending.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_fulfilled = StatCard(self.kpi_frame, title="Delivered & Received", value="0", subtitle="Stock accepted by pharmacy", icon="✅")
        self.card_fulfilled.grid(row=0, column=2, sticky="nsew", padx=6)

        self.card_business = StatCard(self.kpi_frame, title="Total Invoiced Value", value="₹0.00", subtitle="Gross trade volume", icon="💰")
        self.card_business.grid(row=0, column=3, sticky="nsew", padx=6)

        # 3. Tab Navigation
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_CARD, corner_radius=12)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.tab_orders = self.tabview.add("Inbound Purchase Orders")
        self.tab_catalog = self.tabview.add("Supplied Medicine Catalog")
        self.tab_ledger = self.tabview.add("Payment & Invoicing Ledger")

        self._build_orders_tab()
        self._build_catalog_tab()
        self._build_ledger_tab()

    def _build_orders_tab(self):
        tab = self.tab_orders
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))

        ctk.CTkLabel(toolbar, text="Purchase Orders Assigned to Your Distribution Firm", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")

        ctk.CTkButton(
            toolbar,
            text="✍ Respond / Confirm Selected PO",
            font=accessibility_manager.get_font(11, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=self._on_respond_po
        ).pack(side="right")

        cols = [
            {"key": "po_number", "title": "PO Number", "width": 110, "anchor": "w"},
            {"key": "order_date", "title": "Date Issued", "width": 110, "anchor": "center"},
            {"key": "status", "title": "Fulfillment Status", "width": 110, "anchor": "center"},
            {"key": "total_amount", "title": "Order Value (₹)", "width": 120, "anchor": "e"},
            {"key": "items_count", "title": "Items", "width": 80, "anchor": "center"},
            {"key": "notes", "title": "Pharmacy Instructions", "width": 200, "anchor": "w"},
            {"key": "supplier_notes", "title": "Your Quotation / Dispatch Note", "width": 220, "anchor": "w"},
        ]
        self.tbl_orders = DataTable(tab, columns=cols, on_row_select=self._on_select_order)
        self.tbl_orders.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.selected_order = None

    def _build_catalog_tab(self):
        tab = self.tab_catalog
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        cols = [
            {"key": "medicine_name", "title": "Pharmaceutical Item Supplied", "width": 240, "anchor": "w"},
            {"key": "batch_number", "title": "Manufacturer Lot #", "width": 140, "anchor": "w"},
            {"key": "cost_price", "title": "Contract Supply Price (₹)", "width": 150, "anchor": "e"},
            {"key": "current_stock", "title": "Dispensary On-Hand", "width": 130, "anchor": "e"},
            {"key": "expiry_date", "title": "Batch Expiry Date", "width": 120, "anchor": "center"},
        ]
        self.tbl_catalog = DataTable(tab, columns=cols)
        self.tbl_catalog.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _build_ledger_tab(self):
        tab = self.tab_ledger
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        cols = [
            {"key": "purchase_date", "title": "Billing Date", "width": 120, "anchor": "center"},
            {"key": "invoice_number", "title": "Vendor Bill Number", "width": 180, "anchor": "w"},
            {"key": "total_amount", "title": "Invoice Amount (₹)", "width": 150, "anchor": "e"},
            {"key": "payment_status", "title": "Settlement Status", "width": 140, "anchor": "center"},
        ]
        self.tbl_ledger = DataTable(tab, columns=cols)
        self.tbl_ledger.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def load_data(self):
        try:
            metrics = self.api_client.get_supplier_portal_dashboard()
            self.card_orders.update_value(str(metrics.get("assigned_orders", 0)))
            self.card_pending.update_value(str(metrics.get("pending_confirmation", 0)))
            self.card_fulfilled.update_value(str(metrics.get("completed_orders", 0)))
            self.card_business.update_value(f"₹{metrics.get('total_business_value', 0):,.2f}")

            orders = self.api_client.list_supplier_portal_orders()
            self.tbl_orders.set_data(orders)

            catalog = self.api_client.get_supplier_catalog()
            self.tbl_catalog.set_data(catalog)

            ledger = self.api_client.get_supplier_payment_ledger()
            self.tbl_ledger.set_data(ledger)
        except Exception:
            pass

    def _on_select_order(self, row: Dict[str, Any]):
        self.selected_order = row

    def _on_respond_po(self):
        if not self.selected_order:
            return
        RespondPOModal(self.winfo_toplevel(), self.api_client, self.selected_order, on_responded=self.load_data)


class RespondPOModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, po_data: Dict[str, Any], on_responded: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.po_data = po_data
        self.on_responded = on_responded

        self.title(f"Respond to Purchase Order: {po_data.get('po_number')}")
        self.geometry("460x380")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"🚚 Respond to {self.po_data.get('po_number')}", font=accessibility_manager.get_font(15, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 6))
        ctk.CTkLabel(container, text=f"Value: ₹{self.po_data.get('total_amount', 0):,.2f} | Notes: {self.po_data.get('notes') or 'None'}", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(container, text="Fulfillment Response *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.cmb_status = ctk.CTkComboBox(container, values=["Confirmed", "Shipped", "Rejected"], height=32, font=accessibility_manager.get_font(12))
        self.cmb_status.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(container, text="Quotation & Delivery Notes *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_notes = ctk.CTkTextbox(container, height=80, font=accessibility_manager.get_font(12))
        self.txt_notes.pack(fill="x", padx=20, pady=(0, 12))
        self.txt_notes.insert("1.0", "Confirmed. Dispatched via temperature-monitored courier.")

        ctk.CTkButton(
            container,
            text="Transmit Response to Pharmacy",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=20, pady=(4, 16))

    def _submit(self):
        st = self.cmb_status.get()
        notes = self.txt_notes.get("1.0", "end").strip()
        po_id = self.po_data.get("id")
        try:
            self.api_client.respond_supplier_order(po_id, st, notes)
            self.destroy()
            self.on_responded()
        except Exception:
            pass
