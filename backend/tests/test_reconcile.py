from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Transaction, Match
from app.services.reconcile import run_reconciliation
from app.services.extract import parse_amount


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def add(db, source, d, desc, amount, ref=None, party=None):
    db.add(Transaction(source=source, txn_date=date.fromisoformat(d), description=desc,
                       amount=Decimal(amount), reference=ref, counterparty=party))


def seed(db):
    add(db, "bank", "2026-10-02", "ACME SUPPLIES INV-1001", "-500.00")
    add(db, "bank", "2026-10-05", "GLOBEX LTD INV-1002", "-1180.00")
    add(db, "bank", "2026-10-07", "OFFICE COFFEE", "-12.50")
    add(db, "bank", "2026-10-07", "OFFICE COFFEE", "-12.50")
    add(db, "invoice", "2026-09-28", "", "500.00", "INV-1001", "Acme Supplies")
    add(db, "invoice", "2026-09-30", "", "1200.00", "INV-1002", "Globex Ltd")
    add(db, "invoice", "2026-10-01", "", "300.00", "INV-1003", "Initech")
    db.commit()


def statuses(db):
    return sorted(m.status for m in db.query(Match).all())


def test_full_scenario(db):
    seed(db)
    run_reconciliation(db)
    assert statuses(db) == ["amount_mismatch", "matched", "possible_duplicate", "unexplained", "unpaid"]


def test_underpayment_difference(db):
    seed(db)
    run_reconciliation(db)
    m = db.query(Match).filter_by(status="amount_mismatch").one()
    assert m.difference == Decimal("20.00")
    assert "underpaid by 20.00" in m.reason


def test_rerun_is_idempotent(db):
    seed(db)
    run_reconciliation(db)
    first = statuses(db)
    run_reconciliation(db)
    assert statuses(db) == first


def test_one_payment_never_matches_two_invoices(db):
    add(db, "bank", "2026-10-02", "PAYMENT 100", "-100.00")
    add(db, "invoice", "2026-09-28", "", "100.00", "A-1", "X")
    add(db, "invoice", "2026-09-29", "", "100.00", "A-2", "X")
    db.commit()
    run_reconciliation(db)
    assert statuses(db).count("unpaid") == 1


@pytest.mark.parametrize("raw,expected", [
    ("1,250.00", "1250.00"), ("(500.00)", "-500.00"), ("$99", "99.00"), ("500.00 DR", "-500.00"),
])
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == Decimal(expected)