from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, Boolean, Float
from .db import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)       # bank_statement | invoice | payment
    file_hash = Column(String, unique=True)         # blocks duplicate uploads
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    source = Column(String, index=True)             # bank | invoice | payment
    txn_date = Column(Date, nullable=False)
    description = Column(Text, default="")
    amount = Column(Numeric(14, 2), nullable=False) # bank: debit negative, credit positive
    reference = Column(String)                      # invoice number etc.
    counterparty = Column(String)                   # vendor / customer
    needs_review = Column(Boolean, default=False)   # extraction couldn't be verified

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    status = Column(String, index=True)  # matched|probable|amount_mismatch|unpaid|unexplained|possible_duplicate
    score = Column(Float, default=0)
    difference = Column(Numeric(14, 2), default=0)
    reason = Column(Text)