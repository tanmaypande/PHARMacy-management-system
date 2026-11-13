import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.ui.components.stat_card import StatCard
from app.ui.components.data_table import DataTable
from app.client.api_client import APIClient


class OwnerView(ctk.CTkFrame):
    """
    Panel 2: Pharmacy Owner Panel
    Proprietor dashboard for commercial pharmacy oversight:
    Financial Profit & Loss, operating expenses, dispensary profile, and staff governance.
    """
    def __init__(self, parent, api_client: APIClient, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__(parent, fg_color=Theme.BG_APP)
        self.api_client = api_client
        self.on_navigate = on_navigate

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
            text="🏢 Pharmacy Owner Commercial Dashboard",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="+ Record Operating Expense",
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_expense_modal
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

        # 2. Financial KPI Cards
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        for col in range(4):
            self.kpi_frame.grid_columnconfigure(col, weight=1)

        self.card_revenue = StatCard(self.kpi_frame, title="Total Revenue", value="₹0.00", subtitle="Paid counter sales", icon="💰")
        self.card_revenue.grid(row=0, column=0, sticky="nsew", padx=6)

        self.card_expenses = StatCard(self.kpi_frame, title="Operating Expenses", value="₹0.00", subtitle="Rent, power, salaries", icon="📉")
        self.card_expenses.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_net_profit = StatCard(self.kpi_frame, title="Net Operating Profit", value="₹0.00", subtitle="Gross revenue minus spend", icon="📈")
        self.card_net_profit.grid(row=0, column=2, sticky="nsew", padx=6)

        self.card_staff = StatCard(self.kpi_frame, title="Active Employees", value="0", subtitle="Pharmacists & cashiers", icon="👥")
        self.card_staff.grid(row=0, column=3, sticky="nsew", padx=6)

        # 3. Tab Navigation
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_CARD, corner_radius=12)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.tab_pnl = self.tabview.add("Profit & Loss Statement")
        self.tab_expenses = self.tabview.add("Operating Expenses Ledger")
        self.tab_profile = self.tabview.add("Dispensary Profile & License")

        self._build_pnl_tab()
        self._build_expenses_tab()
        self._build_profile_tab()

    def _build_pnl_tab(self):
        tab = self.tab_pnl
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        # Left Column: Financial Breakdown Cards
        left_frame = ctk.CTkFrame(tab, fg_color=Theme.BG_MUTED, corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        ctk.CTkLabel(left_frame, text="📊 Financial Income & Margin Statement", font=accessibility_manager.get_font(14, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=16, pady=(14, 10))

        self.lbl_pnl_sales = self._make_stat_row(left_frame, "Gross Counter Sales (Revenue):", "₹0.00")
        self.lbl_pnl_cogs = self._make_stat_row(left_frame, "Cost of Goods Procured (Purchases):", "₹0.00")
        self.lbl_pnl_margin = self._make_stat_row(left_frame, "Gross Merchandise Margin:", "₹0.00")
        self.lbl_pnl_exp = self._make_stat_row(left_frame, "Total Operating Overhead (Expenses):", "₹0.00")

        div = ctk.CTkFrame(left_frame, height=1, fg_color=Theme.BORDER)
        div.pack(fill="x", padx=16, pady=8)

        self.lbl_pnl_net = self._make_stat_row(left_frame, "Net Commercial Profit:", "₹0.00", is_bold=True)
        self.lbl_pnl_pct = self._make_stat_row(left_frame, "Net Margin Percentage:", "0.0%", is_bold=True)

        # Right Column: Expenses by Category
        right_frame = ctk.CTkFrame(tab, fg_color=Theme.BG_MUTED, corner_radius=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

        ctk.CTkLabel(right_frame, text="🏷️ Expense Distribution by Category", font=accessibility_manager.get_font(14, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=16, pady=(14, 10))

        self.expense_breakdown_box = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.expense_breakdown_box.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    def _make_stat_row(self, parent, label: str, value: str, is_bold: bool = False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row, text=label, font=accessibility_manager.get_font(12), text_color=Theme.TEXT_MUTED).pack(side="left")
        val_lbl = ctk.CTkLabel(row, text=value, font=accessibility_manager.get_font(13, weight="bold" if is_bold else "normal"), text_color=Theme.TEXT_MAIN)
        val_lbl.pack(side="right")
        return val_lbl

    def _build_expenses_tab(self):
        tab = self.tab_expenses
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))

        ctk.CTkLabel(toolbar, text="Dispensary Operating Expenses Log", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")

        cols = [
            {"key": "expense_date", "title": "Date", "width": 110, "anchor": "center"},
            {"key": "category", "title": "Expense Category", "width": 140, "anchor": "w"},
            {"key": "amount", "title": "Amount (₹)", "width": 120, "anchor": "e"},
            {"key": "description", "title": "Details / Note", "width": 260, "anchor": "w"},
            {"key": "recorded_by", "title": "Recorded By", "width": 120, "anchor": "w"},
        ]
        self.tbl_expenses = DataTable(
            tab,
            columns=cols,
            on_action_click=self._on_delete_expense,
            action_button_text="Delete"
        )
        self.tbl_expenses.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_profile_tab(self):
        tab = self.tab_profile
        tab.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(tab, fg_color=Theme.BG_MUTED, corner_radius=10, width=540)
        container.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(container, text="Dispensary Commercial Profile", font=accessibility_manager.get_font(15, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 10))

        self.txt_prof_name = self._make_input(container, "Pharmacy Trade Name", "")
        self.txt_prof_lic = self._make_input(container, "Drug Controller License No (Locked)", "", state="disabled")
        self.txt_prof_phone = self._make_input(container, "Phone Number", "")
        self.txt_prof_email = self._make_input(container, "Official Email", "")
        self.txt_prof_addr = self._make_input(container, "Physical Dispensary Address", "")

        ctk.CTkButton(
            container,
            text="Save Profile Updates",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._save_profile
        ).pack(anchor="e", padx=20, pady=(10, 16))

    def _make_input(self, parent, label: str, val: str, state: str = "normal"):
        ctk.CTkLabel(parent, text=label, font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        entry = ctk.CTkEntry(parent, height=32, font=accessibility_manager.get_font(12), state=state)
        entry.pack(fill="x", padx=20, pady=(0, 4))
        entry.insert(0, val)
        return entry

    def load_data(self):
        try:
            # 1. Dashboard
            metrics = self.api_client.get_owner_dashboard()
            rev = metrics.get("total_revenue", 0.0)
            exp = metrics.get("total_expenses", 0.0)
            net = metrics.get("net_profit", 0.0)
            self.card_revenue.update_value(f"₹{rev:,.2f}")
            self.card_expenses.update_value(f"₹{exp:,.2f}")
            self.card_net_profit.update_value(f"₹{net:,.2f}")
            self.card_staff.update_value(str(metrics.get("total_employees", 0)))

            # 2. P&L
            pnl = self.api_client.get_profit_and_loss()
            self.lbl_pnl_sales.configure(text=f"₹{pnl.get('gross_sales', 0):,.2f}")
            self.lbl_pnl_cogs.configure(text=f"₹{pnl.get('cost_of_goods_sold', 0):,.2f}")
            self.lbl_pnl_margin.configure(text=f"₹{pnl.get('gross_margin', 0):,.2f}")
            self.lbl_pnl_exp.configure(text=f"₹{pnl.get('total_expenses', 0):,.2f}")
            self.lbl_pnl_net.configure(text=f"₹{pnl.get('net_profit', 0):,.2f}")
            self.lbl_pnl_pct.configure(text=f"{pnl.get('net_margin_percentage', 0):.1f}%")

            # Render breakdown
            for w in self.expense_breakdown_box.winfo_children():
                w.destroy()
            for b in pnl.get("expenses_breakdown", []):
                row = ctk.CTkFrame(self.expense_breakdown_box, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"• {b['category']}", font=accessibility_manager.get_font(12), text_color=Theme.TEXT_MAIN).pack(side="left")
                ctk.CTkLabel(row, text=f"₹{b['amount']:,.2f}", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="right")

            # 3. Expenses table
            expenses = self.api_client.list_expenses()
            self.tbl_expenses.set_data(expenses)

            # 4. Profile
            prof = self.api_client.get_pharmacy_profile()
            self.txt_prof_name.delete(0, "end")
            self.txt_prof_name.insert(0, prof.get("name", ""))
            self.txt_prof_lic.configure(state="normal")
            self.txt_prof_lic.delete(0, "end")
            self.txt_prof_lic.insert(0, prof.get("license_number", ""))
            self.txt_prof_lic.configure(state="disabled")
            self.txt_prof_phone.delete(0, "end")
            self.txt_prof_phone.insert(0, prof.get("phone", ""))
            self.txt_prof_email.delete(0, "end")
            self.txt_prof_email.insert(0, prof.get("email", ""))
            self.txt_prof_addr.delete(0, "end")
            self.txt_prof_addr.insert(0, prof.get("address", ""))
        except Exception:
            pass

    def _open_expense_modal(self):
        AddExpenseModal(self.winfo_toplevel(), self.api_client, on_saved=self.load_data)

    def _on_delete_expense(self, row: Dict[str, Any]):
        e_id = row.get("id")
        if e_id:
            try:
                self.api_client.delete_expense(e_id)
                self.load_data()
            except Exception:
                pass

    def _save_profile(self):
        payload = {
            "name": self.txt_prof_name.get().strip(),
            "phone": self.txt_prof_phone.get().strip(),
            "email": self.txt_prof_email.get().strip(),
            "address": self.txt_prof_addr.get().strip()
        }
        try:
            self.api_client.update_pharmacy_profile(payload)
            self.load_data()
        except Exception:
            pass


class AddExpenseModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, on_saved: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.on_saved = on_saved

        self.title("Record Operating Expense")
        self.geometry("440x420")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="📉 Record Expense", font=accessibility_manager.get_font(16, weight="bold"), text_color=Theme.TEXT_MAIN).pack(pady=(16, 12))

        ctk.CTkLabel(container, text="Expense Category *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.cmb_cat = ctk.CTkComboBox(container, values=["Rent", "Utilities", "Salaries", "Supplies", "Maintenance", "Packaging", "Other"], height=32, font=accessibility_manager.get_font(12))
        self.cmb_cat.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(container, text="Amount (₹) *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.txt_amount = ctk.CTkEntry(container, placeholder_text="0.00", height=32, font=accessibility_manager.get_font(12))
        self.txt_amount.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(container, text="Description / Purpose *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=24, pady=(4, 2))
        self.txt_desc = ctk.CTkEntry(container, placeholder_text="e.g. Monthly electricity bill", height=32, font=accessibility_manager.get_font(12))
        self.txt_desc.pack(fill="x", padx=24, pady=(0, 10))

        self.lbl_err = ctk.CTkLabel(container, text="", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.DANGER_TEXT)
        self.lbl_err.pack(pady=2)

        ctk.CTkButton(
            container,
            text="Add Operating Expense",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=24, pady=(8, 16))

    def _submit(self):
        cat = self.cmb_cat.get()
        amt_str = self.txt_amount.get().strip()
        desc = self.txt_desc.get().strip()

        if not amt_str or not desc:
            self.lbl_err.configure(text="Please specify amount and purpose.")
            return

        try:
            amt = float(amt_str)
            if amt <= 0:
                self.lbl_err.configure(text="Amount must be positive.")
                return
            self.api_client.add_expense(category=cat, amount=amt, description=desc)
            self.destroy()
            self.on_saved()
        except ValueError:
            self.lbl_err.configure(text="Invalid amount entered.")
        except Exception as e:
            self.lbl_err.configure(text=str(e)[:45])
