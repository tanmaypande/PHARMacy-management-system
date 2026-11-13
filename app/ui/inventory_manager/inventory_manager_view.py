import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.ui.components.stat_card import StatCard
from app.ui.components.data_table import DataTable
from app.client.api_client import APIClient


class InventoryManagerView(ctk.CTkFrame):
    """
    Panel 5: Inventory Manager Panel
    Controls stock levels, batch expiry dates, wholesale purchase orders (Workflow B),
    goods receiving, physical adjustments with audit trails, and stock movements.
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
            text="📦 Inventory & Warehouse Logistics Management",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="+ Create Purchase Order",
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_create_po_modal
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions_box,
            text="⚖️ Adjust Physical Stock",
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MAIN,
            command=self._open_adjustment_modal
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions_box,
            text="↻ Refresh",
            width=80,
            font=accessibility_manager.get_font(12),
            fg_color=Theme.BG_MUTED,
            text_color=Theme.TEXT_MAIN,
            command=self.load_data
        ).pack(side="left")

        # 2. KPI Cards
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        for col in range(4):
            self.kpi_frame.grid_columnconfigure(col, weight=1)

        self.card_units = StatCard(self.kpi_frame, title="Total Stock Units", value="0", subtitle="Physical dispensary count", icon="📦")
        self.card_units.grid(row=0, column=0, sticky="nsew", padx=6)

        self.card_batches = StatCard(self.kpi_frame, title="Active Batches", value="0", subtitle="Tracked lot numbers", icon="🏷️")
        self.card_batches.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_reorders = StatCard(self.kpi_frame, title="Low Stock Items", value="0", subtitle="Below reorder threshold", icon="⚠️")
        self.card_reorders.grid(row=0, column=2, sticky="nsew", padx=6)

        self.card_expired = StatCard(self.kpi_frame, title="Expired Batches", value="0", subtitle="Blocked from dispensing", icon="🚫")
        self.card_expired.grid(row=0, column=3, sticky="nsew", padx=6)

        # 3. Tab Navigation
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_CARD, corner_radius=12)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.tab_pos = self.tabview.add("Wholesale Purchase Orders")
        self.tab_movements = self.tabview.add("TQM Stock Movement Ledger")
        self.tab_inventory = self.tabview.add("Batch Inventory & Lots")

        self._build_po_tab()
        self._build_movements_tab()
        self._build_inventory_tab()

    def _build_po_tab(self):
        tab = self.tab_pos
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))

        ctk.CTkLabel(toolbar, text="Filter by Order Status:", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=(0, 8))
        self.cmb_po_status = ctk.CTkComboBox(toolbar, values=["All", "Pending", "Confirmed", "Shipped", "Received", "Rejected"], width=130, command=lambda v: self.load_data())
        self.cmb_po_status.pack(side="left")

        ctk.CTkButton(
            toolbar,
            text="📥 Receive Stock Delivery",
            font=accessibility_manager.get_font(11, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=self._on_receive_selected_po
        ).pack(side="right")

        cols = [
            {"key": "po_number", "title": "PO Number", "width": 110, "anchor": "w"},
            {"key": "supplier_name", "title": "Distributor / Supplier", "width": 180, "anchor": "w"},
            {"key": "order_date", "title": "Ordered Date", "width": 110, "anchor": "center"},
            {"key": "status", "title": "Order Status", "width": 100, "anchor": "center"},
            {"key": "total_amount", "title": "Total Amount (₹)", "width": 120, "anchor": "e"},
            {"key": "items_count", "title": "Line Items", "width": 90, "anchor": "center"},
            {"key": "notes", "title": "Order Notes", "width": 160, "anchor": "w"},
            {"key": "supplier_notes", "title": "Supplier Quotation Notes", "width": 180, "anchor": "w"},
        ]
        self.tbl_pos = DataTable(tab, columns=cols, on_row_select=self._on_select_po)
        self.tbl_pos.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.selected_po = None

    def _build_movements_tab(self):
        tab = self.tab_movements
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))
        ctk.CTkLabel(toolbar, text="Immutable Audit Trail of All Physical Stock Movements", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")

        cols = [
            {"key": "timestamp", "title": "Timestamp", "width": 130, "anchor": "center"},
            {"key": "medicine_name", "title": "Pharmaceutical Item", "width": 200, "anchor": "w"},
            {"key": "batch_number", "title": "Batch Number", "width": 120, "anchor": "w"},
            {"key": "movement_type", "title": "Movement Type", "width": 110, "anchor": "center"},
            {"key": "quantity_change", "title": "Qty Change", "width": 100, "anchor": "e"},
            {"key": "balance_after", "title": "Resulting Stock", "width": 110, "anchor": "e"},
            {"key": "performed_by", "title": "Actor", "width": 110, "anchor": "w"},
            {"key": "reason", "title": "Reason / Justification", "width": 240, "anchor": "w"},
        ]
        self.tbl_movements = DataTable(tab, columns=cols)
        self.tbl_movements.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_inventory_tab(self):
        tab = self.tab_inventory
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        cols = [
            {"key": "medicine_name", "title": "Medicine Formulation", "width": 220, "anchor": "w"},
            {"key": "batch_number", "title": "Batch Lot #", "width": 130, "anchor": "w"},
            {"key": "cost_price", "title": "Unit Cost (₹)", "width": 110, "anchor": "e"},
            {"key": "selling_price", "title": "Retail MRP (₹)", "width": 110, "anchor": "e"},
            {"key": "current_stock", "title": "Stock Units", "width": 100, "anchor": "e"},
            {"key": "expiry_date", "title": "Expiry Date", "width": 110, "anchor": "center"},
            {"key": "status", "title": "Status Alert", "width": 120, "anchor": "center"},
        ]
        self.tbl_inventory = DataTable(tab, columns=cols)
        self.tbl_inventory.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def load_data(self):
        try:
            # Metrics
            metrics = self.api_client.get_dashboard_metrics()
            self.card_units.update_value(str(metrics.get("total_stock_units", 0)))
            self.card_batches.update_value(str(metrics.get("total_batches", 0)))
            self.card_reorders.update_value(str(metrics.get("low_stock_medicines", 0)))
            self.card_expired.update_value(str(metrics.get("expired_batches", 0)))

            # POs
            st = self.cmb_po_status.get()
            orders = self.api_client.list_purchase_orders(status=st)
            self.tbl_pos.set_data(orders)

            # Movements
            movements = self.api_client.list_stock_movements()
            self.tbl_movements.set_data(movements)

            # Batches
            batches = self.api_client.list_batches()
            b_data = []
            for b in batches:
                is_exp = b.get("is_expired", False)
                days = b.get("days_until_expiry", 999)
                alert = "🔴 EXPIRED" if is_exp else ("🟡 NEAR EXPIRY" if days <= 30 else "🟢 IN STOCK")
                b_data.append({
                    "medicine_name": b.get("medicine_name") or "Medicine",
                    "batch_number": b.get("batch_number") or "",
                    "cost_price": f"₹{b.get('cost_price', 0):.2f}",
                    "selling_price": f"₹{b.get('selling_price', 0):.2f}",
                    "current_stock": b.get("quantity", 0),
                    "expiry_date": str(b.get("expiry_date", "")),
                    "status": alert
                })
            self.tbl_inventory.set_data(b_data)
        except Exception:
            pass

    def _on_select_po(self, row: Dict[str, Any]):
        self.selected_po = row

    def _open_create_po_modal(self):
        CreatePurchaseOrderModal(self.winfo_toplevel(), self.api_client, on_created=self.load_data)

    def _on_receive_selected_po(self):
        if not self.selected_po:
            return
        ReceiveGoodsModal(self.winfo_toplevel(), self.api_client, self.selected_po, on_received=self.load_data)

    def _open_adjustment_modal(self):
        AdjustStockModal(self.winfo_toplevel(), self.api_client, on_adjusted=self.load_data)


class CreatePurchaseOrderModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, on_created: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.on_created = on_created

        self.title("Create Wholesale Purchase Order")
        self.geometry("500x520")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="🛒 Issue Purchase Order", font=accessibility_manager.get_font(16, weight="bold"), text_color=Theme.TEXT_MAIN).pack(pady=(16, 12))

        # Supplier dropdown
        ctk.CTkLabel(container, text="Select Distributor / Supplier *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.suppliers = self.api_client.list_suppliers()
        supp_names = [s.get("name", "Supplier") for s in self.suppliers] or ["No Suppliers Registered"]
        self.cmb_supplier = ctk.CTkComboBox(container, values=supp_names, height=32, font=accessibility_manager.get_font(12))
        self.cmb_supplier.pack(fill="x", padx=24, pady=(0, 6))

        # Medicine dropdown
        ctk.CTkLabel(container, text="Select Medicine Formulation *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.medicines = self.api_client.list_medicines()
        med_names = [m.get("name", "Medicine") for m in self.medicines] or ["No Medicines"]
        self.cmb_medicine = ctk.CTkComboBox(container, values=med_names, height=32, font=accessibility_manager.get_font(12))
        self.cmb_medicine.pack(fill="x", padx=24, pady=(0, 6))

        # Quantity and unit cost
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=4)

        col1 = ctk.CTkFrame(row, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(col1, text="Order Units *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.txt_qty = ctk.CTkEntry(col1, placeholder_text="e.g. 200", height=32)
        self.txt_qty.pack(fill="x")

        col2 = ctk.CTkFrame(row, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(col2, text="Expected Unit Cost (₹) *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.txt_cost = ctk.CTkEntry(col2, placeholder_text="e.g. 18.50", height=32)
        self.txt_cost.pack(fill="x")

        ctk.CTkLabel(container, text="Order Notes / Delivery Instructions", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(8, 2))
        self.txt_notes = ctk.CTkEntry(container, placeholder_text="Delivery by Friday, temperature controlled", height=32)
        self.txt_notes.pack(fill="x", padx=24, pady=(0, 10))

        self.lbl_err = ctk.CTkLabel(container, text="", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.DANGER_TEXT)
        self.lbl_err.pack(pady=2)

        ctk.CTkButton(
            container,
            text="Generate & Transmit Purchase Order",
            height=38,
            font=accessibility_manager.get_font(13, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=24, pady=(8, 16))

    def _submit(self):
        supp_name = self.cmb_supplier.get()
        med_name = self.cmb_medicine.get()
        qty_str = self.txt_qty.get().strip()
        cost_str = self.txt_cost.get().strip()

        if not qty_str or not cost_str:
            self.lbl_err.configure(text="Quantity and cost price are required.")
            return

        supp_id = next((s["id"] for s in self.suppliers if s.get("name") == supp_name), None)
        med_id = next((m["id"] for m in self.medicines if m.get("name") == med_name), None)

        if not supp_id or not med_id:
            self.lbl_err.configure(text="Please select valid supplier and medicine.")
            return

        try:
            qty = int(qty_str)
            cost = float(cost_str)
            self.api_client.create_purchase_order({
                "supplier_id": supp_id,
                "items": [{"medicine_id": med_id, "quantity": qty, "unit_cost_price": cost}],
                "notes": self.txt_notes.get().strip()
            })
            self.destroy()
            self.on_created()
        except Exception as e:
            self.lbl_err.configure(text=str(e)[:45])


class ReceiveGoodsModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, po_data: Dict[str, Any], on_received: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.po_data = po_data
        self.on_received = on_received

        self.title(f"Receive Goods Delivery for {po_data.get('po_number')}")
        self.geometry("480x440")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"📥 Receive PO: {self.po_data.get('po_number')}", font=accessibility_manager.get_font(15, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(16, 4))
        ctk.CTkLabel(container, text=f"Supplier: {self.po_data.get('supplier_name')} | Value: ₹{self.po_data.get('total_amount', 0):,.2f}", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 10))

        ctk.CTkLabel(container, text="Batch / Lot Number Stamped *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.txt_lot = ctk.CTkEntry(container, placeholder_text=f"LOT-{datetime.now(timezone.utc).strftime('%m%d%H%M')}", height=32)
        self.txt_lot.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(container, text="Quantity Received *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.txt_qty = ctk.CTkEntry(container, placeholder_text="100", height=32)
        self.txt_qty.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(container, text="Expiry Date (YYYY-MM-DD) *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.txt_exp = ctk.CTkEntry(container, placeholder_text="2028-12-31", height=32)
        self.txt_exp.pack(fill="x", padx=24, pady=(0, 6))
        self.txt_exp.insert(0, "2028-12-31")

        ctk.CTkButton(
            container,
            text="Confirm Goods Receiving & Restock Inventory",
            height=38,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=24, pady=(14, 16))

    def _submit(self):
        po_id = self.po_data.get("id")
        lot = self.txt_lot.get().strip() or f"LOT-{datetime.now(timezone.utc).strftime('%m%d%H%M')}"
        qty_str = self.txt_qty.get().strip() or "100"
        exp = self.txt_exp.get().strip() or "2028-12-31"

        try:
            po_details = self.api_client.get_purchase_order_details(po_id)
            items = po_details.get("items", [])
            med_id = items[0]["medicine_id"] if items else None
            cost = items[0]["unit_cost_price"] if items else 20.0

            if not med_id:
                meds = self.api_client.list_medicines()
                med_id = meds[0]["id"] if meds else None

            batches_payload = [{
                "medicine_id": med_id,
                "quantity": int(qty_str),
                "cost_price": float(cost),
                "selling_price": float(cost) * 1.25,
                "batch_number": lot,
                "expiry_date": exp
            }]

            self.api_client.receive_purchase_order_goods(po_id, batches_payload)
            self.destroy()
            self.on_received()
        except Exception:
            pass


class AdjustStockModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, on_adjusted: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.on_adjusted = on_adjusted

        self.title("Physical Stock Count Adjustment")
        self.geometry("450x420")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="⚖️ Stock Count Adjustment", font=accessibility_manager.get_font(16, weight="bold"), text_color=Theme.TEXT_MAIN).pack(pady=(16, 12))

        # Batch dropdown
        ctk.CTkLabel(container, text="Select Medicine Batch *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.batches = self.api_client.list_batches()
        b_names = [f"{b.get('medicine_name')} ({b.get('batch_number')}) — Qty: {b.get('quantity')}" for b in self.batches] or ["No Batches"]
        self.cmb_batch = ctk.CTkComboBox(container, values=b_names, height=32, font=accessibility_manager.get_font(12))
        self.cmb_batch.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(container, text="Verified Physical Quantity * (≥ 0)", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.txt_qty = ctk.CTkEntry(container, placeholder_text="Enter counted physical quantity", height=32)
        self.txt_qty.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(container, text="Mandatory TQM Audit Reason *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.cmb_reason = ctk.CTkComboBox(container, values=["Physical cycle count discrepancy", "Damaged packaging / broken vials", "Quality audit sample extraction", "Found misplaced stock in secondary rack"], height=32, font=accessibility_manager.get_font(12))
        self.cmb_reason.pack(fill="x", padx=24, pady=(0, 10))

        self.lbl_err = ctk.CTkLabel(container, text="", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.DANGER_TEXT)
        self.lbl_err.pack(pady=2)

        ctk.CTkButton(
            container,
            text="Record Stock Adjustment in Audit Ledger",
            height=38,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=24, pady=(10, 16))

    def _submit(self):
        qty_str = self.txt_qty.get().strip()
        reason = self.cmb_reason.get()

        if not qty_str:
            self.lbl_err.configure(text="Please enter the verified physical count.")
            return

        try:
            qty = int(qty_str)
            if qty < 0:
                self.lbl_err.configure(text="TQM Rule: Stock cannot be negative.")
                return

            sel_idx = self.cmb_batch._values.index(self.cmb_batch.get()) if self.cmb_batch.get() in self.cmb_batch._values else 0
            batch_id = self.batches[sel_idx]["id"]

            self.api_client.adjust_inventory_stock(batch_id, qty, reason)
            self.destroy()
            self.on_adjusted()
        except ValueError:
            self.lbl_err.configure(text="Invalid quantity number entered.")
        except Exception as e:
            self.lbl_err.configure(text=str(e)[:45])
