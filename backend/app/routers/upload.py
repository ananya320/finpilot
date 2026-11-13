import hashlib
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Document, Transaction
from ..services.extract import extract
from ..services import vectorstore

router = APIRouter()
SOURCE = {"bank_statement": "bank", "invoice": "invoice", "payment": "payment"}

@router.post("/upload")
async def upload(file: UploadFile = File(...), doc_type: str = Form(...), db: Session = Depends(get_db)):
    if doc_type not in SOURCE:
        raise HTTPException(400, "doc_type must be bank_statement, invoice or payment")
    data = await file.read()
    h = hashlib.sha256(data).hexdigest()
    if db.query(Document).filter_by(file_hash=h).first():
        raise HTTPException(409, "This exact file was already uploaded.")
    try:
        rows, rejected, text = extract(data, file.filename, doc_type)
    except Exception as e:
        raise HTTPException(422, f"Could not process file: {e}")

    doc = Document(filename=file.filename, doc_type=doc_type, file_hash=h)
    db.add(doc); db.flush()
    for r in rows:
        amt = r["amount"]
        if doc_type == "invoice":   amt = abs(amt)    # amount owed, positive
        if doc_type == "payment":   amt = -abs(amt)   # money out, negative (same as bank debits)
        db.add(Transaction(document_id=doc.id, source=SOURCE[doc_type], **{**r, "amount": amt}))
    db.commit()

    try:
        vectorstore.index_text(doc.id, file.filename, text)
    except Exception:
        pass  # search index is optional; never fail an upload because of it
    return {"document_id": doc.id, "saved": len(rows),
            "needs_review": sum(r["needs_review"] for r in rows), "rejected": rejected}