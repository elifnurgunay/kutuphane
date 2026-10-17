"""Aynı nüsha iki eşzamanlı istekte yalnızca bir kez ödünç verilir.

SQLite'ta dosya tabanlı veritabanıyla, `TEST_POSTGRES_URL` tanımlıysa ayrıca
PostgreSQL'de (SELECT ... FOR UPDATE) çalışır. Örnek:
    TEST_POSTGRES_URL=postgresql+psycopg://kutuphane:kutuphane@localhost:5433/kutuphane_test
"""

import os
import threading
from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.db import Base
from app.core.errors import AppError, ErrorCode
from app.models import Book, BookCopy, Loan, Member, User
from app.models.enums import CopyStatus, MemberType, UserRole
from app.services import loan_service, settings_service

TODAY = date(2026, 10, 17)


def _engine(backend: str, tmp_path):
    if backend == "sqlite":
        return create_engine(
            f"sqlite:///{tmp_path / 'concurrency.db'}",
            connect_args={"check_same_thread": False, "timeout": 10},
        )
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL tanımlı değil")
    return create_engine(url)


@pytest.mark.parametrize("backend", ["sqlite", "postgres"])
def test_same_copy_is_issued_only_once(backend, tmp_path):
    engine = _engine(backend, tmp_path)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine, expire_on_commit=False)

    with make_session() as db:
        settings_service.ensure_defaults(db)
        staff = User(
            email="g@test.local", password_hash="x", full_name="G", role=UserRole.LIBRARIAN
        )
        members = [
            Member(
                user=User(
                    email=f"u{i}@test.local", password_hash="x", full_name="U", role=UserRole.MEMBER
                ),
                member_no=f"UYE-{i:06d}",
                member_type=MemberType.STUDENT,
                membership_start=date(2026, 1, 1),
                membership_end=date(2027, 1, 1),
            )
            for i in (1, 2)
        ]
        copy = BookCopy(book=Book(title="Tek Nüsha"), barcode="KTP-0001-01")
        db.add_all([staff, *members, copy])
        db.commit()
        staff_id, member_ids = staff.id, [m.id for m in members]

    barrier = threading.Barrier(2)
    results: list[object] = []

    def borrow(member_id: int) -> None:
        with make_session() as db:
            staff = db.get(User, staff_id)
            barrier.wait()
            try:
                loan_service.issue_loan(db, member_id, "KTP-0001-01", staff, today=TODAY)
                results.append("ok")
            except AppError as exc:
                results.append(exc.code)
            except OperationalError:
                # SQLite eşzamanlı yazmada birini "database is locked" ile reddedebilir
                results.append("locked")

    threads = [threading.Thread(target=borrow, args=(member_id,)) for member_id in member_ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    with Session(engine) as db:
        assert db.scalar(select(func.count(Loan.id))) == 1
        assert db.scalar(select(BookCopy.status)) == CopyStatus.LOANED
    assert results.count("ok") == 1
    loser = next(r for r in results if r != "ok")
    if backend == "postgres":
        assert loser == ErrorCode.COPY_NOT_AVAILABLE
    else:
        assert loser in (ErrorCode.COPY_NOT_AVAILABLE, "locked")

    Base.metadata.drop_all(engine)
    engine.dispose()
