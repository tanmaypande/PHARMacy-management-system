import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge


class SettingsView(ctk.CTkFrame):
    """
    Healthcare SaaS Accessibility, Store Identity, and Application Settings View.
    Fulfills TQM Goal Q12 — Improve Accessibility with:
    - Default Light Theme, Dark Theme, and High-Contrast Mode
    - Dynamic font scaling (100% - 140%) with live font recalculation
    - Pharmacy Store Identity & GSTIN Configuration
    - One-Click Disaster Recovery Database Backup
    - Non-color-exclusive status indicators
    """
    def __init__(self, master, api_client=None, on_theme_change=None):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.on_theme_change = on_theme_change
        self._build_ui()
        if self.api_client:
            self._load_store_settings()

    def _build_ui(self):
        # Scrollable container so all settings fit comfortably at any scaling
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        # Header Title
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            hdr,
            text="Accessibility & System Preferences",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            hdr,
            text="Configure UI visual contrast, dynamic font scaling, and review TQM Q12 compliance standards.",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # ---------------- Section 1: Appearance & Visual Themes ----------------
        card_theme = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        card_theme.pack(fill="x", pady=(0, 16))

        t_header = ctk.CTkFrame(card_theme, fg_color="transparent")
        t_header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            t_header,
            text="🎨 Visual Theme & Contrast Mode",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        StatusBadge(t_header, text="Q12 Accessibility Core", variant="info").pack(side="right")

        ctk.CTkLabel(
            card_theme,
            text="Select an interface appearance tailored for clinical lighting, low-light environments, or high-contrast visibility.",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 14))

        self.theme_var = ctk.StringVar(value=accessibility_manager.config.get("appearance_mode", "light"))
        modes_row = ctk.CTkFrame(card_theme, fg_color="transparent")
        modes_row.pack(fill="x", padx=20, pady=(0, 20))

        themes = [
            ("Light Mode (Default)", "light", "Clean medical aesthetic, optimized for daylight clinic environments"),
            ("Dark Mode", "dark", "Reduced glare and eye fatigue for night shifts"),
            ("High Contrast (Q12)", "high-contrast", "Maximum contrast ratio (WCAG AAA) for vision-impaired operators")
        ]

        for label, val, desc in themes:
            btn_box = ctk.CTkFrame(modes_row, fg_color=Theme.BG_MUTED, corner_radius=8)
            btn_box.pack(fill="x", pady=4)

            rb = ctk.CTkRadioButton(
                btn_box,
                text=label,
                value=val,
                variable=self.theme_var,
                command=self._apply_theme,
                font=accessibility_manager.get_font(13, weight="bold"),
                fg_color=Theme.PRIMARY[0],
                hover_color=Theme.PRIMARY_HOVER[0]
            )
            rb.pack(anchor="w", padx=16, pady=(10, 2))

            ctk.CTkLabel(
                btn_box,
                text=f"   {desc}",
                font=accessibility_manager.get_font(11),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", padx=16, pady=(0, 10))

        # ---------------- Section 2: Dynamic Font Scaling ----------------
        card_font = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        card_font.pack(fill="x", pady=(0, 16))

        f_header = ctk.CTkFrame(card_font, fg_color="transparent")
        f_header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            f_header,
            text="🔍 Dynamic Font Scaling",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        current_scale = int(accessibility_manager.config.get("font_scale", 1.0) * 100)
        self.scale_badge = StatusBadge(f_header, text=f"{current_scale}% Scale", variant="success")
        self.scale_badge.pack(side="right")

        ctk.CTkLabel(
            card_font,
            text="Adjust overall text scaling proportionally across tables, form inputs, buttons, and navigation labels.",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 14))

        slider_box = ctk.CTkFrame(card_font, fg_color="transparent")
        slider_box.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(slider_box, text="100%", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left")

        self.slider = ctk.CTkSlider(
            slider_box,
            from_=1.0,
            to=1.4,
            number_of_steps=4,
            command=self._on_slider_change,
            fg_color=Theme.BORDER,
            progress_color=Theme.PRIMARY[0]
        )
        self.slider.set(accessibility_manager.config.get("font_scale", 1.0))
        self.slider.pack(side="left", fill="x", expand=True, padx=14)

        ctk.CTkLabel(slider_box, text="140%", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left")

        # Quick Preset Buttons
        presets_box = ctk.CTkFrame(card_font, fg_color="transparent")
        presets_box.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(
            presets_box,
            text="Quick Presets:",
            font=accessibility_manager.get_font(12, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(side="left", padx=(0, 8))

        presets = [
            (1.0, "100% Standard"),
            (1.1, "110% Medium"),
            (1.2, "120% Large"),
            (1.3, "130% Extra Large"),
            (1.4, "140% Maximum")
        ]
        for scale_val, label in presets:
            ctk.CTkButton(
                presets_box,
                text=label,
                height=30,
                corner_radius=8,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                font=accessibility_manager.get_font(11, weight="bold"),
                command=lambda v=scale_val: self._set_preset(v)
            ).pack(side="left", padx=4)

        # Live Font Preview Box
        preview_box = ctk.CTkFrame(card_font, fg_color=Theme.BG_MUTED, corner_radius=8)
        preview_box.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            preview_box,
            text="Live Typography Preview:",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=14, pady=(8, 2))

        self.lbl_preview = ctk.CTkLabel(
            preview_box,
            text="Amoxicillin 500mg • Batch #AMX-9021 • 150 Units In-Stock • Expiry: 2026-12-31",
            font=accessibility_manager.get_font(13),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_preview.pack(anchor="w", padx=14, pady=(0, 10))

        # ---------------- Section 3: Pharmacy Store Profile & GSTIN ----------------
        card_store = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        card_store.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card_store,
            text="🏥 Pharmacy Business Identity & Billing Header",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            card_store,
            text="Printed on customer receipts, invoices, and regulatory compliance documents.",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 12))

        s_box = ctk.CTkFrame(card_store, fg_color="transparent")
        s_box.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(s_box, text="Pharmacy Trade Name *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_store_name = ctk.CTkEntry(s_box, height=36)
        self.entry_store_name.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(s_box, text="Store Address", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_store_addr = ctk.CTkEntry(s_box, height=36)
        self.entry_store_addr.pack(fill="x", pady=(2, 8))

        row_gst = ctk.CTkFrame(s_box, fg_color="transparent")
        row_gst.pack(fill="x", pady=(0, 8))

        c_gst = ctk.CTkFrame(row_gst, fg_color="transparent")
        c_gst.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(c_gst, text="GSTIN / Drug License #", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_store_gst = ctk.CTkEntry(c_gst, height=36)
        self.entry_store_gst.pack(fill="x", pady=(2, 0))

        c_ph = ctk.CTkFrame(row_gst, fg_color="transparent")
        c_ph.pack(side="right", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(c_ph, text="Contact Phone", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_store_phone = ctk.CTkEntry(c_ph, height=36)
        self.entry_store_phone.pack(fill="x", pady=(2, 0))

        btn_save_store = ctk.CTkButton(
            s_box,
            text="💾 Save Store Profile",
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._save_store_settings
        )
        btn_save_store.pack(anchor="w", pady=(10, 0))

        # ---------------- Section 4: Disaster Recovery & Database Backup ----------------
        card_backup = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        card_backup.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card_backup,
            text="💾 Disaster Recovery & Database Backup",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            card_backup,
            text="Generates an offline point-in-time PostgreSQL snapshot for audit and disaster protection.",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 12))

        b_box = ctk.CTkFrame(card_backup, fg_color="transparent")
        b_box.pack(fill="x", padx=20, pady=(0, 16))

        self.btn_backup = ctk.CTkButton(
            b_box,
            text="⚡ Create Instant Database Backup",
            height=36,
            fg_color=Theme.SECONDARY,
            text_color=Theme.SECONDARY_TEXT,
            command=self._trigger_backup
        )
        self.btn_backup.pack(side="left", padx=(0, 10))

        self.lbl_backup_status = ctk.CTkLabel(
            b_box,
            text="Status: Ready",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_backup_status.pack(side="left")

        # ---------------- Section 5: TQM Q12 Quality & Architecture Controls ----------------
        card_tqm = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        card_tqm.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card_tqm,
            text="🛡️ TQM System Architecture & Quality Verification",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            card_tqm,
            text="Technical standards and poka-yoke defect prevention safeguards enforced in this deployment:",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 12))

        safeguards = [
            ("Decoupled Client Architecture", "CustomTkinter UI communicates via REST API only. Zero direct database handles in UI.", "success"),
            ("Poka-Yoke Expiry Blocking", "Batches expiring in the past or on receipt day are rejected at API and service layers.", "success"),
            ("Decimal Financial Precision", "Prices and subtotals calculated using standard Python Decimal arithmetic to prevent float errors.", "success"),
            ("Relational Check Constraints", "Non-negative stock quantities and non-empty medicine SKU identifiers enforced.", "success"),
            ("Q12 Multi-Sensory Indicators", "Status badges pair symbols (●, ▲, 🛑) with descriptive text for colorblind operators.", "info")
        ]

        for title, desc, variant in safeguards:
            row = ctk.CTkFrame(card_tqm, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", padx=20, pady=3)

            StatusBadge(row, text="VERIFIED", variant=variant, width=90).pack(side="left", padx=10, pady=8)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=4, pady=6)

            ctk.CTkLabel(info, text=title, font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
            ctk.CTkLabel(info, text=desc, font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MUTED).pack(anchor="w")

        ctk.CTkLabel(card_tqm, text="", height=4).pack()

    def _apply_theme(self):
        new_mode = self.theme_var.get()
        accessibility_manager.set_appearance_mode(new_mode)
        if self.on_theme_change:
            self.on_theme_change("theme")

    def _set_preset(self, val: float):
        self.slider.set(val)
        self._on_slider_change(val)

    def _load_store_settings(self):
        from app.ui.common.async_task import run_in_background
        def _fetch():
            return self.api_client.get_store_settings()

        def _on_done(settings):
            if not settings:
                return
            if "store_name" in settings:
                self.entry_store_name.delete(0, "end")
                self.entry_store_name.insert(0, settings["store_name"])
            if "store_address" in settings:
                self.entry_store_addr.delete(0, "end")
                self.entry_store_addr.insert(0, settings["store_address"])
            if "store_gstin" in settings:
                self.entry_store_gst.delete(0, "end")
                self.entry_store_gst.insert(0, settings["store_gstin"])
            if "store_phone" in settings:
                self.entry_store_phone.delete(0, "end")
                self.entry_store_phone.insert(0, settings["store_phone"])

        run_in_background(_fetch, on_success=_on_done)

    def _save_store_settings(self):
        from app.ui.common.async_task import run_in_background
        import tkinter.messagebox as msg

        payload = {
            "store_name": self.entry_store_name.get().strip() or "MediCare Pharmacy",
            "store_address": self.entry_store_addr.get().strip(),
            "store_gstin": self.entry_store_gst.get().strip(),
            "store_phone": self.entry_store_phone.get().strip(),
        }

        def _do():
            return self.api_client.update_store_settings(payload)

        run_in_background(_do, on_success=lambda _: msg.showinfo("Settings Saved", "Store profile updated successfully!"))

    def _trigger_backup(self):
        from app.ui.common.async_task import run_in_background
        self.btn_backup.configure(state="disabled", text="Backing up...")
        self.lbl_backup_status.configure(text="Creating snapshot...")

        def _do():
            return self.api_client.create_backup()

        def _on_done(res):
            self.btn_backup.configure(state="normal", text="⚡ Create Instant Database Backup")
            self.lbl_backup_status.configure(text=f"Backup Saved: {res.get('file_path')}")

        run_in_background(_do, on_success=_on_done)

    def _on_slider_change(self, val: float):
        pct = int(round(val * 100))
        self.scale_badge.update_text(f"{pct}% Scale")
        accessibility_manager.set_font_scale(val)
        if self.on_theme_change:
            self.on_theme_change("font_scale")
