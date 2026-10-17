from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"
    MEMBER = "member"


class MemberType(StrEnum):
    STUDENT = "student"
    STAFF = "staff"
    PUBLIC = "public"


class MemberStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class CopyStatus(StrEnum):
    AVAILABLE = "available"
    LOANED = "loaned"
    RESERVED = "reserved"
    LOST = "lost"
    DAMAGED = "damaged"
    MAINTENANCE = "maintenance"


class LoanStatus(StrEnum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"


class ReservationStatus(StrEnum):
    WAITING = "waiting"
    READY = "ready"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class FineReason(StrEnum):
    OVERDUE = "overdue"
    LOST = "lost"
    DAMAGED = "damaged"


class FineStatus(StrEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    WAIVED = "waived"
