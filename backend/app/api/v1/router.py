from fastapi import APIRouter

from app.api.v1 import auth, books, catalog, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(books.books)
api_router.include_router(books.copies)
api_router.include_router(catalog.authors)
api_router.include_router(catalog.publishers)
api_router.include_router(catalog.categories)
