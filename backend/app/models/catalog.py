from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, enum_column
from app.models.enums import CopyStatus

book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
)

book_categories = Table(
    "book_categories",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    birth_year: Mapped[int | None]
    bio: Mapped[str | None] = mapped_column(Text)

    books: Mapped[list[Book]] = relationship(secondary=book_authors, back_populates="authors")


class Publisher(Base):
    __tablename__ = "publishers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)

    books: Mapped[list[Book]] = relationship(back_populates="publisher")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))

    parent: Mapped[Category | None] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    books: Mapped[list[Book]] = relationship(secondary=book_categories, back_populates="categories")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    subtitle: Mapped[str | None] = mapped_column(String(255))
    publisher_id: Mapped[int | None] = mapped_column(ForeignKey("publishers.id"))
    publish_year: Mapped[int | None]
    page_count: Mapped[int | None]
    language: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    publisher: Mapped[Publisher | None] = relationship(back_populates="books")
    authors: Mapped[list[Author]] = relationship(secondary=book_authors, back_populates="books")
    categories: Mapped[list[Category]] = relationship(
        secondary=book_categories, back_populates="books"
    )
    copies: Mapped[list[BookCopy]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


class BookCopy(Base):
    __tablename__ = "book_copies"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    barcode: Mapped[str] = mapped_column(String(50), unique=True)
    shelf_location: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[CopyStatus] = mapped_column(
        enum_column(CopyStatus), default=CopyStatus.AVAILABLE, index=True
    )
    acquired_at: Mapped[date | None]
    notes: Mapped[str | None] = mapped_column(Text)

    book: Mapped[Book] = relationship(back_populates="copies")
