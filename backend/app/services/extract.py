import io, re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

import pymupdf as fitz   # PyMuPDF
import pandas as pd
from dateutil import parser as dateparser
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import settings

DAYFIRST = True  # ambiguous dates like 03/04/2026 are read as 3 April. Change for US formats.

ALIASES = {
    "date": ["date", "txn date", "transaction date", "posting date", "value date", "invoice date"],
    "description": ["description", "narration", "details", "particulars", "memo", "remarks"],
    "debit": ["debit", "withdrawal", "withdrawals", "dr", "money out"],
    "credit": ["credit", "deposit", "deposits", "cr", "money in"],
    "amount": ["amount", "total", "invoice amount", "value"],
    "reference": ["reference", "ref", "invoice number", "invoice no", "invoice_number", "inv no"],
    "counterparty": ["vendor", "supplier", "customer", "counterparty", "payee", "party"],
}

# ---------- helpers ----------
def parse_amount(v) -> Decimal:
    if v is None or (isinstance(v, float) and v != v) or str(v).strip() == "":
        return Decimal("0")
    s = str(v).strip()
    neg = s.startswith("(") and s.endswith(")") or s.endswith("-") or s.upper().endswith("DR")
    s = re.sub(r"[^\d.\-]", "", s.replace(",", ""))
    s = s.strip("-")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"unreadable amount: {v!r}")
    d = -d if neg else d
    return d.quantize(Decimal("0.01"))

def parse_date(v) -> date:
    s = str(v).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return date.fromisoformat(s)
    return dateparser.parse(s, dayfirst=DAYFIRST).date()

def _norm(c: str) -> str:
    return re.sub(r"\s+", " ", str(c).strip().lower())

# ---------- CSV / Excel ----------
def rows_from_dataframe(df: pd.DataFrame):
    mapping = {}
    for key, names in ALIASES.items():
        for col in df.columns:
            if _norm(col) in names:
                mapping[key] = col
                break
    if "date" not in mapping or not ("amount" in mapping or "debit" in mapping or "credit" in mapping):
        raise ValueError(f"Could not find date/amount columns. Found: {list(df.columns)}")

    rows, rejected = [], []
    for i, r in df.iterrows():
        try:
            d = parse_date(r[mapping["date"]])
            if "amount" in mapping:
                amt = parse_amount(r[mapping["amount"]])
            else:
                amt = parse_amount(r.get(mapping.get("credit"))) - parse_amount(r.get(mapping.get("debit")))
            if amt == 0:
                raise ValueError("zero or missing amount")
            get = lambda k: (str(r[mapping[k]]).strip() if k in mapping and pd.notna(r[mapping[k]]) else None)
            rows.append(dict(txn_date=d, amount=amt, description=get("description") or "",
                             reference=get("reference"), counterparty=get("counterparty"), needs_review=False))
        except Exception as e:
            rejected.append(f"Row {i + 2}: {e}")
    return rows, rejected

# ---------- PDF ----------
class ExtractedTxn(BaseModel):
    date: str                      # YYYY-MM-DD
    description: str
    amount: str                    # signed decimal string, money out negative
    reference: Optional[str] = None
    counterparty: Optional[str] = None

class Extraction(BaseModel):
    transactions: list[ExtractedTxn]

RULES = (
    "Extract ONLY what is literally printed. Never infer, estimate or invent values. "
    "Dates must be YYYY-MM-DD; skip a row if its date cannot be determined. "
    "Amounts are plain decimal strings like -1250.00 (no currency symbols or commas). "
)
PROMPTS = {
    "bank_statement": RULES + "Extract every transaction row. Money leaving the account is negative, money received is positive. "
                      "Skip opening/closing balances, running balances and headers.",
    "invoice": RULES + "Return exactly ONE transaction for the invoice: date = invoice date, reference = invoice number, "
               "counterparty = vendor name, amount = the final total payable (positive).",
    "payment": RULES + "Extract each payment as a transaction (amount positive), with reference/invoice number if shown.",
}

def pdf_pages(data: bytes) -> list[str]:
    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for p in doc:
        text = p.get_text()
        if len(text.strip()) < 20:  # probably scanned, so try OCR (needs Tesseract installed)
            try:
                text = p.get_textpage_ocr(full=True).extractText()
            except Exception:
                text = ""
        pages.append(text)
    return pages

def _llm():
    return ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.google_api_key,
                                  temperature=0).with_structured_output(Extraction)

def _grounded(amount: Decimal, text: str) -> bool:
    flat = text.replace(",", "").replace(" ", "")
    return f"{abs(amount):.2f}" in flat

def extract_pdf(data: bytes, doc_type: str):
    pages = pdf_pages(data)
    if not any(p.strip() for p in pages):
        raise ValueError("No readable text in PDF (is it scanned? install Tesseract for OCR).")
    # statements page by page (long); invoices/payments as one chunk
    chunks = pages if doc_type == "bank_statement" else ["\n".join(pages)]
    rows, rejected = [], []
    for chunk in chunks:
        if not chunk.strip():
            continue
        result = _llm().invoke(f"{PROMPTS[doc_type]}\n\nDOCUMENT TEXT:\n{chunk}")
        for t in result.transactions:
            try:
                amt = parse_amount(t.amount)
                rows.append(dict(txn_date=parse_date(t.date), amount=amt, description=t.description,
                                 reference=t.reference, counterparty=t.counterparty,
                                 needs_review=not _grounded(amt, chunk)))
            except Exception as e:
                rejected.append(f"{t.description[:40]}: {e}")
    return rows, rejected, "\n".join(pages)

# ---------- entry point ----------
def extract(data: bytes, filename: str, doc_type: str):
    """Returns (rows, rejected, raw_text_for_search)."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return extract_pdf(data, doc_type)
    if name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(data), dtype=str)
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(data), dtype=str)
    else:
        raise ValueError("Unsupported file type. Use PDF, CSV or XLSX.")
    rows, rejected = rows_from_dataframe(df)
    return rows, rejected, df.to_csv(index=False)