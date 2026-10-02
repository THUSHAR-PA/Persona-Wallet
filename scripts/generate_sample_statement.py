"""Reproduce the fictional six-month fixture. ReportLab is needed only for PDF output."""

import csv
from calendar import monthrange
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = []
balance = Decimal("125000.00")
for month in range(4, 10):
    events = [
        (
            1,
            "SALARY - Demo Software Studio",
            0,
            85000 if month < 7 else 90000,
            "SALARY",
        ),
        (3, "Home mortgage EMI", 24500, 0, "EMI"),
        (5, "Education loan EMI", 6500, 0, "EMI"),
        (6, "Mutual fund SIP", 8000, 0, "INVESTMENT"),
        (7, "Health insurance premium", 1800, 0, "INSURANCE"),
        (8, "Electricity bill", 2200 + month * 20, 0, "UTILITIES"),
        (9, "Broadband bill", 899, 0, "UTILITIES"),
        (10, "Housing maintenance", 1500, 0, "OTHER"),
        (12, "Freelance design income", 0, 5000, "OTHER_INCOME"),
        (13, "Fuel station", 1700, 0, "TRANSPORT"),
        (16, "Own account self transfer", 5000, 0, "TRANSFER"),
        (18, "Mobile recharge", 399, 0, "UTILITIES"),
        (20, "Clothing shopping", 1200 + month * 100, 0, "SHOPPING"),
        (22, "Pharmacy medicines", 900 if month != 8 else 12900, 0, "HEALTHCARE"),
        (24, "Online education course", 999, 0, "EDUCATION"),
        (25, "Streaming subscription", 499, 0, "SUBSCRIPTION"),
        (26, "Fuel station", 1700, 0, "TRANSPORT"),
        (monthrange(2026, month)[1], "Savings interest credit", 0, 100, "OTHER_INCOME"),
    ]
    events += [
        (day, "Grocery supermarket", 550 + month * 15 + day * 3, 0, "GROCERIES")
        for day in (2, 5, 8, 11, 14, 17, 20, 23, 26, 28)
    ]
    events += [
        (day, "Restaurant dining", 350 + day * 8, 0, "DINING")
        for day in (4, 7, 11, 15, 19, 23, 27)
    ]
    events += [(day, "Metro transport", 140, 0, "TRANSPORT") for day in (6, 12, 18, 24)]
    for day, description, debit, credit, category in sorted(
        events, key=lambda event: event[0]
    ):
        balance += Decimal(credit) - Decimal(debit)
        rows.append(
            [
                date(2026, month, day).isoformat(),
                description,
                f"{debit:.2f}" if debit else "",
                f"{credit:.2f}" if credit else "",
                f"{balance:.2f}",
                f"DEMO-{len(rows) + 1:05d}",
                category,
            ]
        )

csv_path = ROOT / "backend/data/sample-bank-statement.csv"
csv_path.parent.mkdir(parents=True, exist_ok=True)
with csv_path.open("w", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(
        ["Date", "Description", "Debit", "Credit", "Balance", "Reference", "Category"]
    )
    writer.writerows(rows)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

pdf_path = ROOT / "backend/data/sample-bank-statement.pdf"
pdf_path.parent.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=landscape(A4),
    rightMargin=30,
    leftMargin=30,
    topMargin=34,
    bottomMargin=34,
)
story = [
    Paragraph("EXAMPLE BANK / FICTIONAL STATEMENT", styles["Title"]),
    Paragraph(
        "Persona Wallet analysis fixture - no real customer or bank data",
        styles["Normal"],
    ),
    Spacer(1, 12),
    Paragraph(
        "Account: Demo salary account | Masked account: ****4821 | Currency: INR",
        styles["Normal"],
    ),
    Paragraph(
        f"Period: 01 April 2026 - 30 September 2026 | Opening: INR 125,000.00 | Closing: INR {balance:,.2f}",
        styles["Normal"],
    ),
    Paragraph(
        "Includes salary, freelance income, home mortgage, education loan, household expenses and investments.",
        styles["Normal"],
    ),
    Spacer(1, 16),
]
headers = ["Date", "Description", "Debit", "Credit", "Balance", "Reference", "Category"]
formatted = [
    [
        *row[:2],
        *[f"{Decimal(value):,.2f}" if value else "" for value in row[2:5]],
        *row[5:],
    ]
    for row in rows
]
table = Table(
    [headers] + formatted, colWidths=[66, 190, 72, 72, 86, 84, 104], repeatRows=1
)
table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (2, 1), (4, -1), "RIGHT"),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#f1f5f9")],
            ),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
)
story.append(table)


def footer(canvas, document):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(30, 18, "FICTIONAL DEMO DATA - not a real bank statement")
    canvas.drawRightString(812, 18, f"Page {document.page}")


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(
    f"{len(rows)} transactions; closing INR {balance}; CSV: {csv_path}; PDF: {pdf_path}"
)
