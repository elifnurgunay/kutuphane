from app.core.errors import AppError, ErrorCode


def _isbn10_valid(isbn: str) -> bool:
    if not (isbn[:9].isdigit() and (isbn[9].isdigit() or isbn[9] == "X")):
        return False
    digits = [10 if c == "X" else int(c) for c in isbn]
    return sum((10 - i) * d for i, d in enumerate(digits)) % 11 == 0


def _isbn13_valid(isbn: str) -> bool:
    if not isbn.isdigit():
        return False
    return sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(isbn)) % 10 == 0


def normalize_isbn(raw: str | None) -> str | None:
    """Tire/boşlukları atar ve ISBN-10 veya ISBN-13 sağlama hanesini doğrular."""
    if raw is None or not raw.strip():
        return None
    isbn = raw.replace("-", "").replace(" ", "").upper()
    valid = (len(isbn) == 10 and _isbn10_valid(isbn)) or (len(isbn) == 13 and _isbn13_valid(isbn))
    if not valid:
        raise AppError(ErrorCode.INVALID_ISBN, "Geçersiz ISBN numarası.", 400)
    return isbn
