import hashlib

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_business
from ..models import Document, Transaction, Match, Business
from ..services.extract import extract
from ..services import vectorstore

router = APIRouter()
SOURCE = {"bank_statement": "bank", "invoice": "invoice", "payment": "payment"}
MAX_BYTES = 10 * 1024 * 1024


@router.post("/upload")
async def upload(file: UploadFile = File(...), doc_type: str = Form(...),
                 biz: Business = Depends(current_business), db: Session = Depends(get_db)):
    if doc_type not in SOURCE:
        raise HTTPException(400, "doc_type must be bank_statement, invoice or payment")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File is larger than 10MB.")
    h = hashlib.sha256(data).hexdigest()
    if db.query(Document).filter_by(business_id=biz.id, file_hash=h).first():
        raise HTTPException(409, "This exact file was already uploaded.")
    try:
        rows, rejected, text = extract(data, file.filename, doc_type)
    except Exception as e:
        raise HTTPException(422, f"Could not process file: {e}")

    doc = Document(business_id=biz.id, filename=file.filename, doc_type=doc_type,
                   file_hash=h, size=len(data))
    db.add(doc)
    db.flush()
    for r in rows:
        amt = r["amount"]
        if doc_type == "invoice":
            amt = abs(amt)
        if doc_type == "payment":
            amt = -abs(amt)
        db.add(Transaction(business_id=biz.id, document_id=doc.id, source=SOURCE[doc_type],
                           **{**r, "amount": amt}))
    db.commit()

    try:
        vectorstore.index_text(doc.id, biz.id, file.filename, text)
    except Exception:
        pass  # search index is optional
    return {"document_id": doc.id, "filename": file.filename, "saved": len(rows),
            "needs_review": sum(r["needs_review"] for r in rows), "rejected": rejected}


@router.get("/documents")
def documents(biz: Business = Depends(current_business), db: Session = Depends(get_db)):
    docs = db.query(Document).filter_by(business_id=biz.id).order_by(Document.id.desc()).all()
    counts = dict(db.query(Transaction.document_id, func.count(Transaction.id))
                    .filter(Transaction.business_id == biz.id)
                    .group_by(Transaction.document_id).all())
    return [dict(id=d.id, filename=d.filename, doc_type=d.doc_type, size=d.size or 0,
                 created=d.created_at.isoformat(), rows=counts.get(d.id, 0)) for d in docs]


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, biz: Business = Depends(current_business),
                    db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc or doc.business_id != biz.id:
        raise HTTPException(404, "File not found")
    db.query(Match).filter(Match.business_id == biz.id).delete()   # results are now stale
    db.query(Transaction).filter(Transaction.document_id == doc_id).delete()
    db.delete(doc)
    db.commit()
    try:
        vectorstore.delete_document(doc_id)
    except Exception:
        pass
    return {"deleted": doc_id}