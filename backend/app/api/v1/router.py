from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    books,
    catalog,
    health,
    loans,
    me,
    members,
    reports,
    reservations,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(books.books)
api_router.include_router(books.copies)
api_router.include_router(catalog.authors)
api_router.include_router(catalog.publishers)
api_router.include_router(catalog.categories)
api_router.include_router(members.router)
api_router.include_router(loans.router)
api_router.include_router(reservations.reservations)
api_router.include_router(reservations.fines)
api_router.include_router(me.router)
api_router.include_router(reports.router)
api_router.include_router(admin.settings)
api_router.include_router(admin.staff)
api_router.include_router(admin.audit_logs)
