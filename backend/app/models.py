from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, Date, DateTime, Numeric,
                        ForeignKey, Boolean, Float, UniqueConstraint)
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    currency = Column(String, default="$")          # display symbol only
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("business_id", "file_hash", name="uq_doc_business_hash"),)
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), index=True)
    filename = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)       # bank_statement | invoice | payment
    file_hash = Column(String)                      # blocks duplicate uploads per business
    size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    source = Column(String, index=True)             # bank | invoice | payment
    txn_date = Column(Date, nullable=False)
    description = Column(Text, default="")
    amount = Column(Numeric(14, 2), nullable=False)
    reference = Column(String)
    counterparty = Column(String)
    needs_review = Column(Boolean, default=False)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), index=True)
    invoice_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    status = Column(String, index=True)
    score = Column(Float, default=0)
    difference = Column(Numeric(14, 2), default=0)
    reason = Column(Text)