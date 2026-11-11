import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_invoice_pdf(sale_data: Dict[str, Any], output_path: str, store_info: Dict[str, Any] = None) -> str:
    """
    Generates a professional, print-ready PDF invoice for patient dispensation.
    Adheres to commercial pharmacy standards and TQM billing accuracy.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#0D9488"),
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14
    )
    bold_style = ParagraphStyle(
        "BoldText",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1E293B")
    )
    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # Store Header
    store_name = (store_info or {}).get("store_name", "MediCare Pharmacy Ltd.")
    store_addr = (store_info or {}).get("store_address", "102 Health Avenue, Medical District")
    store_gstin = (store_info or {}).get("store_gstin", "GSTIN: 27AABCM8234M1Z2")
    store_phone = (store_info or {}).get("store_phone", "Ph: +91 98765 43210")

    story.append(Paragraph(f"<b>{store_name}</b>", title_style))
    story.append(Paragraph(f"{store_addr} | {store_phone} | {store_gstin}", sub_style))
    story.append(Spacer(1, 10))

    # Invoice Details Bar
    inv_num = sale_data.get("invoice_number", "INV-SAMPLE")
    sale_date = sale_data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    cust_name = sale_data.get("customer_name") or "Walk-in Customer"
    cust_phone = sale_data.get("customer_phone") or "N/A"
    pay_method = sale_data.get("payment_method", "Cash")

    info_data = [
        [
            Paragraph(f"<b>Invoice #:</b> {inv_num}", normal_style),
            Paragraph(f"<b>Patient / Customer:</b> {cust_name}", normal_style)
        ],
        [
            Paragraph(f"<b>Date:</b> {sale_date}", normal_style),
            Paragraph(f"<b>Phone:</b> {cust_phone}", normal_style)
        ],
        [
            Paragraph(f"<b>Payment:</b> {pay_method}", normal_style),
            Paragraph(f"<b>Status:</b> {sale_data.get('status', 'COMPLETED')}", normal_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # Line Items Table
    headers = ["#", "Medicine Description", "Batch #", "Qty", "Unit Price (₹)", "Total (₹)"]
    table_rows = [[Paragraph(f"<b>{h}</b>", bold_style) for h in headers]]

    items = sale_data.get("items", [])
    for idx, item in enumerate(items, 1):
        table_rows.append([
            Paragraph(str(idx), normal_style),
            Paragraph(item.get("medicine_name", "Medicine"), normal_style),
            Paragraph(item.get("batch_number", "LOT"), normal_style),
            Paragraph(str(item.get("quantity", 1)), normal_style),
            Paragraph(f"₹{float(item.get('unit_price', 0)):.2f}", normal_style),
            Paragraph(f"₹{float(item.get('subtotal', 0)):.2f}", normal_style),
        ])

    items_table = Table(table_rows, colWidths=[30, 210, 80, 40, 90, 90])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 14))

    # Totals Summary Table
    subtotal = float(sale_data.get("subtotal", 0))
    tax_amt = float(sale_data.get("tax_amount", 0))
    discount_amt = float(sale_data.get("discount_amount", 0))
    total_amt = float(sale_data.get("total_amount", 0))

    summary_data = [
        ["Subtotal:", f"₹{subtotal:.2f}"],
        ["Discount:", f"- ₹{discount_amt:.2f}"],
        ["GST / Tax:", f"+ ₹{tax_amt:.2f}"],
        ["Grand Total:", f"₹{total_amt:.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[120, 100], hAlign="RIGHT")
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#0D9488")),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor("#0D9488")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 24))

    # Footer Notice
    footer_text = "Thank you for your visit! Dispensed medicines should be kept out of reach of children."
    story.append(Paragraph(f"<i>{footer_text}</i>", sub_style))

    doc.build(story)
    return output_path
