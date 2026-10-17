from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.db import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import User
from app.models.enums import UserRole
from app.services import settings_service

DEFAULT_PASSWORD = "Parola123!"


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        settings_service.ensure_defaults(session)
        yield session
    engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    def _make_user(
        role: UserRole = UserRole.MEMBER,
        email: str | None = None,
        password: str = DEFAULT_PASSWORD,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email or f"{role.value}{db.query(User).count() + 1}@test.local",
            password_hash=hash_password(password),
            full_name=f"Test {role.value}",
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        return user

    return _make_user
