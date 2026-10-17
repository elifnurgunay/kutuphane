"""Testlerde ortak kullanılan küçük veri kurucuları."""

from datetime import UTC, date, datetime, timedelta

from app.core.security import hash_password
from app.models import Book, BookCopy, Loan, Member, Reservation, Setting, User
from app.models.enums import MemberStatus, MemberType, UserRole
from app.services import loan_service as svc

TODAY = date(2026, 10, 17)
NOW = datetime(2026, 10, 17, 10, 0, tzinfo=UTC)


class World:
    """Testler için küçük bir kütüphane: personel, üyeler, kitaplar."""

    def __init__(self, db):
        self.db = db
        self.staff = User(
            email="gorevli@test.local",
            password_hash=hash_password("x"),
            full_name="Görevli",
            role=UserRole.LIBRARIAN,
        )
        db.add(self.staff)
        self._members = 0
        self._books = 0
        db.commit()

    def member(self, member_type=MemberType.STUDENT, **overrides) -> Member:
        self._members += 1
        n = self._members
        fields = {
            "member_no": f"UYE-{n:06d}",
            "member_type": member_type,
            "membership_start": date(2026, 1, 1),
            "membership_end": date(2027, 1, 1),
            "status": MemberStatus.ACTIVE,
        }
        member = Member(
            user=User(
                email=f"uye{n}@test.local",
                password_hash="x",
                full_name=f"Üye {n}",
                role=UserRole.MEMBER,
            ),
            **(fields | overrides),
        )
        self.db.add(member)
        self.db.commit()
        return member

    def book(self, copies: int = 1) -> list[BookCopy]:
        self._books += 1
        book = Book(title=f"Kitap {self._books}")
        items = [
            BookCopy(book=book, barcode=f"KTP-{self._books:04d}-{i:02d}")
            for i in range(1, copies + 1)
        ]
        self.db.add_all([book, *items])
        self.db.commit()
        return items

    def issue(self, member: Member, copy: BookCopy, today: date = TODAY) -> Loan:
        return svc.issue_loan(self.db, member.id, copy.barcode, self.staff, today=today)

    def return_(self, loan: Loan, today: date = TODAY, **kwargs) -> svc.ReturnResult:
        return svc.return_loan(self.db, loan.id, self.staff, today=today, now=NOW, **kwargs)

    def reserve(self, member: Member, copy: BookCopy, minutes: int = 0) -> Reservation:
        reservation = Reservation(
            book_id=copy.book_id,
            member_id=member.id,
            created_at=NOW + timedelta(minutes=minutes),
        )
        self.db.add(reservation)
        self.db.commit()
        return reservation

    def set(self, key: str, value: str) -> None:
        self.db.get(Setting, key).value = value
        self.db.commit()
