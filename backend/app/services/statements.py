"""Strict, reviewable CSV / text-table PDF import. No raw statements are persisted."""

import csv
import hashlib
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

CATEGORIES = (
    "SALARY",
    "OTHER_INCOME",
    "RENT",
    "EMI",
    "GROCERIES",
    "DINING",
    "TRANSPORT",
    "UTILITIES",
    "HEALTHCARE",
    "SHOPPING",
    "INVESTMENT",
    "INSURANCE",
    "EDUCATION",
    "SUBSCRIPTION",
    "TAX",
    "TRANSFER",
    "OTHER",
)
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 2000
ALIASES = {
    "date": {"date", "transactiondate", "txndate", "valuedate"},
    "description": {"description", "narration", "particulars", "transactiondetails"},
    "debit": {"debit", "debitamount", "withdrawal", "withdrawals", "withdrawalamount"},
    "credit": {"credit", "creditamount", "deposit", "deposits", "depositamount"},
    "balance": {"balance", "runningbalance", "closingbalance"},
    "reference": {"reference", "referenceno", "transactionid", "refno", "utr"},
    "category": {"category"},
}


class StatementError(ValueError):
    pass


def normalize(value):
    return re.sub(r"[^a-z]", "", str(value or "").lower())


def money(value, *, allow_negative=False):
    value = str(value or "").strip()
    if value in ("", "-", "--"):
        return None
    negative = value.upper().endswith("DR") or (
        value.startswith("(") and value.endswith(")")
    )
    value = (
        re.sub(r"(?i)(INR|RS\.?|CR|DR)", "", value)
        .replace("₹", "")
        .replace(",", "")
        .replace(" ", "")
        .strip("()")
    )
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise StatementError(f"Invalid amount: {value[:40]}") from exc
    if negative:
        number = -abs(number)
    if not number.is_finite() or abs(number) >= Decimal("10000000000000"):
        raise StatementError("Amount is outside the supported range.")
    if number != number.quantize(Decimal("0.01")) or (
        number < 0 and not allow_negative
    ):
        raise StatementError(
            "Amounts need at most two decimal places and debit/credit must be positive."
        )
    return number.quantize(Decimal("0.01"))


def parse_date(value):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d-%b-%Y", "%d/%m/%y"):
        try:
            result = datetime.strptime(str(value).strip(), fmt).date()
            if result > date.today():
                raise StatementError("Transaction dates cannot be in the future.")
            return result
        except ValueError:
            continue
    raise StatementError("Use YYYY-MM-DD or day-first dates such as DD/MM/YYYY.")


def infer_category(description, direction):
    text = description.lower()
    # Transfers are excluded from income/expense ratios; users must review classification.
    rules = [
        ("TRANSFER", ("self transfer", "own account", "internal transfer")),
        ("SALARY", ("salary", "payroll")),
        ("EMI", ("emi", "mortgage", "loan repayment")),
        ("RENT", ("rent",)),
        ("INVESTMENT", ("sip", "mutual fund", "investment")),
        ("INSURANCE", ("insurance", "premium")),
        ("GROCERIES", ("grocery", "groceries", "supermarket")),
        ("DINING", ("restaurant", "dining", "swiggy", "zomato", "cafe")),
        ("TRANSPORT", ("fuel", "petrol", "uber", "metro", "transport")),
        ("UTILITIES", ("electricity", "broadband", "water bill", "mobile recharge")),
        ("HEALTHCARE", ("hospital", "pharmacy", "medical")),
        ("EDUCATION", ("tuition", "education", "school")),
        ("SUBSCRIPTION", ("netflix", "subscription", "spotify")),
        ("SHOPPING", ("shopping", "amazon", "clothing")),
        ("TAX", ("tax",)),
    ]
    for category, keywords in rules:
        if any(word in text for word in keywords):
            return category
    return "OTHER_INCOME" if direction == "INFLOW" else "OTHER"


def header_map(headers):
    result = {}
    for i, header in enumerate(headers):
        for key, aliases in ALIASES.items():
            if normalize(header) in aliases and key not in result:
                result[key] = i
    return (
        result
        if all(key in result for key in ("date", "description", "debit", "credit"))
        else None
    )


def parse_statement(content, filename):
    if not content or len(content) > MAX_FILE_BYTES:
        raise StatementError("Upload a non-empty CSV or PDF smaller than 5 MB.")
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "csv":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise StatementError("Export the CSV using UTF-8 encoding.") from exc
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        tables = [list(csv.reader(io.StringIO(text), dialect))]
    elif suffix == "pdf":
        import pdfplumber

        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                if len(pdf.pages) > 24:
                    raise StatementError(
                        "PDF statements support up to 24 pages. Use CSV for larger exports."
                    )
                tables = [
                    table for page in pdf.pages for table in page.extract_tables()
                ]
        except StatementError:
            raise
        except Exception as exc:
            raise StatementError(
                "Unable to read this PDF. Export an unlocked text-table PDF or CSV."
            ) from exc
        if not tables:
            raise StatementError(
                "No readable transaction table found. Scanned PDFs need a CSV export."
            )
    else:
        raise StatementError("Supported formats: CSV and text-table PDF.")

    rows = []
    recognized = False
    for table in tables:
        mapping = None
        for cells in table:
            if not any(str(cell or "").strip() for cell in cells):
                continue
            candidate = header_map(cells)
            if candidate:
                mapping = candidate
                recognized = True
                continue
            if mapping is None:
                continue
            row_number = len(rows) + 1
            try:

                def field(key):
                    index = mapping.get(key)
                    return (
                        str(cells[index] or "").strip()
                        if index is not None and index < len(cells)
                        else ""
                    )

                txn_date = parse_date(field("date"))
                description = " ".join(field("description").split())
                reference = field("reference")
                if not description or len(description) > 255 or len(reference) > 120:
                    raise StatementError(
                        "Description is required (max 255 characters); reference max 120."
                    )
                debit, credit = (
                    money(field("debit")) or Decimal(0),
                    money(field("credit")) or Decimal(0),
                )
                if (debit > 0) == (credit > 0):
                    raise StatementError(
                        "Each row needs exactly one positive debit or credit."
                    )
                direction = "OUTFLOW" if debit else "INFLOW"
                category = field("category").upper() or infer_category(
                    description, direction
                )
                if category not in CATEGORIES:
                    raise StatementError(
                        f"Unknown category '{category}'. Use the sample's category names."
                    )
                amount = debit or credit
                # Reference helps distinguish otherwise-identical real transactions.
                identity = "|".join(
                    (
                        txn_date.isoformat(),
                        reference or description.lower(),
                        direction,
                        str(amount),
                    )
                )
                rows.append(
                    {
                        "transaction_date": txn_date,
                        "description": description,
                        "reference": reference,
                        "direction": direction,
                        "amount": amount,
                        "category": category,
                        "balance": money(field("balance"), allow_negative=True),
                        "fingerprint": hashlib.sha256(identity.encode()).hexdigest(),
                    }
                )
                if len(rows) > MAX_ROWS:
                    raise StatementError(
                        f"Statements support at most {MAX_ROWS} transactions."
                    )
            except StatementError as exc:
                raise StatementError(f"Transaction row {row_number}: {exc}") from exc
    if not recognized or not rows:
        raise StatementError(
            "Expected Date, Description, Debit, Credit headers and at least one transaction."
        )
    dates = [row["transaction_date"] for row in rows]
    if dates == sorted(dates, reverse=True) and dates != sorted(dates):
        rows.reverse()
    elif dates != sorted(dates):
        raise StatementError(
            "Rows must be ordered by transaction date, ascending or descending."
        )
    balances = [row["balance"] is not None for row in rows]
    if any(balances) and not all(balances):
        raise StatementError(
            "Provide running balances for every row or leave the balance column empty."
        )
    opening, closing = None, None
    if all(balances):
        first = rows[0]
        signed = first["amount"] if first["direction"] == "INFLOW" else -first["amount"]
        opening = first["balance"] - signed
        running = opening
        for i, row in enumerate(rows, 1):
            running += row["amount"] if row["direction"] == "INFLOW" else -row["amount"]
            if running != row["balance"]:
                raise StatementError(
                    f"Running balance does not reconcile at transaction row {i}."
                )
        closing = running
    return {
        "rows": rows,
        "period_start": rows[0]["transaction_date"],
        "period_end": rows[-1]["transaction_date"],
        "opening_balance": opening,
        "closing_balance": closing,
        "file_hash": hashlib.sha256(content).hexdigest(),
    }
