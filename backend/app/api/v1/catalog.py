"""Yazar, yayınevi ve kategori uç noktaları."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import STAFF_ROLES, CurrentUser, DbSession, require_roles
from app.schemas.catalog import (
    AuthorIn,
    AuthorOut,
    CategoryIn,
    CategoryOut,
    PublisherIn,
    PublisherOut,
)
from app.schemas.common import Page
from app.services import catalog_service as svc

staff_only = [Depends(require_roles(*STAFF_ROLES))]
PageNo = Annotated[int, Query(ge=1)]
LookupSize = Annotated[int, Query(ge=1, le=500)]

authors = APIRouter(prefix="/authors", tags=["authors"])
publishers = APIRouter(prefix="/publishers", tags=["publishers"])
categories = APIRouter(prefix="/categories", tags=["categories"])


# --- Yazar ---


@authors.get("", response_model=Page[AuthorOut])
def list_authors(
    db: DbSession, _user: CurrentUser, q: str | None = None, page: PageNo = 1, size: LookupSize = 50
):
    items, total = svc.list_authors(db, q, page, size)
    return Page(items=items, total=total, page=page, size=size)


@authors.get("/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, db: DbSession, _user: CurrentUser):
    return svc.get_author(db, author_id)


@authors.post("", response_model=AuthorOut, status_code=201, dependencies=staff_only)
def create_author(body: AuthorIn, db: DbSession):
    return svc.create_author(db, body)


@authors.put("/{author_id}", response_model=AuthorOut, dependencies=staff_only)
def update_author(author_id: int, body: AuthorIn, db: DbSession):
    return svc.update_author(db, author_id, body)


@authors.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=staff_only)
def delete_author(author_id: int, db: DbSession) -> None:
    svc.delete_author(db, author_id)


# --- Yayınevi ---


@publishers.get("", response_model=Page[PublisherOut])
def list_publishers(
    db: DbSession, _user: CurrentUser, q: str | None = None, page: PageNo = 1, size: LookupSize = 50
):
    items, total = svc.list_publishers(db, q, page, size)
    return Page(items=items, total=total, page=page, size=size)


@publishers.get("/{publisher_id}", response_model=PublisherOut)
def get_publisher(publisher_id: int, db: DbSession, _user: CurrentUser):
    return svc.get_publisher(db, publisher_id)


@publishers.post("", response_model=PublisherOut, status_code=201, dependencies=staff_only)
def create_publisher(body: PublisherIn, db: DbSession):
    return svc.create_publisher(db, body)


@publishers.put("/{publisher_id}", response_model=PublisherOut, dependencies=staff_only)
def update_publisher(publisher_id: int, body: PublisherIn, db: DbSession):
    return svc.update_publisher(db, publisher_id, body)


@publishers.delete(
    "/{publisher_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=staff_only
)
def delete_publisher(publisher_id: int, db: DbSession) -> None:
    svc.delete_publisher(db, publisher_id)


# --- Kategori ---


@categories.get("", response_model=list[CategoryOut])
def list_categories(db: DbSession, _user: CurrentUser):
    return svc.list_categories(db)


@categories.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: DbSession, _user: CurrentUser):
    return svc.get_category(db, category_id)


@categories.post("", response_model=CategoryOut, status_code=201, dependencies=staff_only)
def create_category(body: CategoryIn, db: DbSession):
    return svc.create_category(db, body)


@categories.put("/{category_id}", response_model=CategoryOut, dependencies=staff_only)
def update_category(category_id: int, body: CategoryIn, db: DbSession):
    return svc.update_category(db, category_id, body)


@categories.delete(
    "/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=staff_only
)
def delete_category(category_id: int, db: DbSession) -> None:
    svc.delete_category(db, category_id)
