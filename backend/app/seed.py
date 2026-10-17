"""Örnek veri yükler: 1 admin, 2 görevli, 20 üye, 100 kitap, 250 nüsha, geçmiş ödünçler.

Kullanım (önce `alembic upgrade head`):
    python -m app.seed
"""

import random
import unicodedata
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import Author, Book, BookCopy, Category, Loan, Member, Publisher, User
from app.models.enums import CopyStatus, LoanStatus, MemberStatus, MemberType, UserRole
from app.services import settings_service

# Varsayılan giriş bilgileri (README'de de listelenir). Yalnızca geliştirme içindir.
ADMIN_LOGIN = ("admin@kutuphane.local", "Admin123!")
LIBRARIAN_PASSWORD = "Gorevli123!"
MEMBER_PASSWORD = "Uye12345!"
EMAIL_DOMAIN = "kutuphane.local"

LIBRARIANS = ["Mehmet Kaya", "Zeynep Demir"]

MEMBERS = [
    "Ayşe Yılmaz",
    "Ali Çelik",
    "Fatma Şahin",
    "Mustafa Yıldız",
    "Emine Aydın",
    "Ahmet Öztürk",
    "Hatice Arslan",
    "Hüseyin Doğan",
    "Elif Kılıç",
    "Murat Aslan",
    "Zehra Çetin",
    "İbrahim Kara",
    "Merve Koç",
    "Hasan Kurt",
    "Esra Özdemir",
    "Burak Şimşek",
    "Selin Polat",
    "Emre Erdoğan",
    "Gizem Güneş",
    "Can Aksoy",
]

CATEGORY_TREE = {
    "Edebiyat": ["Roman", "Öykü", "Şiir"],
    "Bilim Kurgu": [],
    "Polisiye": [],
    "Tarih": [],
    "Felsefe": [],
    "Bilim": [],
    "Psikoloji": [],
    "Çocuk": [],
}

PUBLISHERS = [
    "Yapı Kredi Yayınları",
    "İş Bankası Kültür Yayınları",
    "Can Yayınları",
    "İletişim Yayınları",
    "Everest Yayınları",
    "İthaki Yayınları",
    "Metis Yayınları",
    "Doğan Kitap",
]

# (başlık, yazar, kategori, yayın yılı)
BOOKS: list[tuple[str, str, str, int | None]] = [
    ("Tutunamayanlar", "Oğuz Atay", "Roman", 1972),
    ("Saatleri Ayarlama Enstitüsü", "Ahmet Hamdi Tanpınar", "Roman", 1961),
    ("İnce Memed", "Yaşar Kemal", "Roman", 1955),
    ("Kürk Mantolu Madonna", "Sabahattin Ali", "Roman", 1943),
    ("Çalıkuşu", "Reşat Nuri Güntekin", "Roman", 1922),
    ("Aylak Adam", "Yusuf Atılgan", "Roman", 1959),
    ("Huzur", "Ahmet Hamdi Tanpınar", "Roman", 1949),
    ("Kuyucaklı Yusuf", "Sabahattin Ali", "Roman", 1937),
    ("Masumiyet Müzesi", "Orhan Pamuk", "Roman", 2008),
    ("Benim Adım Kırmızı", "Orhan Pamuk", "Roman", 1998),
    ("Sefiller", "Victor Hugo", "Roman", 1862),
    ("Suç ve Ceza", "Fyodor Dostoyevski", "Roman", 1866),
    ("Karamazov Kardeşler", "Fyodor Dostoyevski", "Roman", 1880),
    ("Anna Karenina", "Lev Tolstoy", "Roman", 1877),
    ("Savaş ve Barış", "Lev Tolstoy", "Roman", 1869),
    ("Madame Bovary", "Gustave Flaubert", "Roman", 1857),
    ("Yüzyıllık Yalnızlık", "Gabriel García Márquez", "Roman", 1967),
    ("Dönüşüm", "Franz Kafka", "Öykü", 1915),
    ("Dava", "Franz Kafka", "Roman", 1925),
    ("Yabancı", "Albert Camus", "Roman", 1942),
    ("Veba", "Albert Camus", "Roman", 1947),
    ("Bülbülü Öldürmek", "Harper Lee", "Roman", 1960),
    ("Fareler ve İnsanlar", "John Steinbeck", "Roman", 1937),
    ("Gazap Üzümleri", "John Steinbeck", "Roman", 1939),
    ("Sineklerin Tanrısı", "William Golding", "Roman", 1954),
    ("Uğultulu Tepeler", "Emily Brontë", "Roman", 1847),
    ("Gurur ve Önyargı", "Jane Austen", "Roman", 1813),
    ("Büyük Umutlar", "Charles Dickens", "Roman", 1861),
    ("Don Kişot", "Miguel de Cervantes", "Roman", 1605),
    ("Bir Delinin Hatıra Defteri", "Nikolay Gogol", "Öykü", 1835),
    ("1984", "George Orwell", "Bilim Kurgu", 1949),
    ("Hayvan Çiftliği", "George Orwell", "Roman", 1945),
    ("Cesur Yeni Dünya", "Aldous Huxley", "Bilim Kurgu", 1932),
    ("Fahrenheit 451", "Ray Bradbury", "Bilim Kurgu", 1953),
    ("Dune", "Frank Herbert", "Bilim Kurgu", 1965),
    ("Vakıf", "Isaac Asimov", "Bilim Kurgu", 1951),
    ("Ben, Robot", "Isaac Asimov", "Bilim Kurgu", 1950),
    ("Otostopçunun Galaksi Rehberi", "Douglas Adams", "Bilim Kurgu", 1979),
    ("Karanlığın Sol Eli", "Ursula K. Le Guin", "Bilim Kurgu", 1969),
    ("Biz", "Yevgeni Zamyatin", "Bilim Kurgu", 1924),
    ("Solaris", "Stanisław Lem", "Bilim Kurgu", 1961),
    ("Zaman Makinesi", "H. G. Wells", "Bilim Kurgu", 1895),
    ("Dünyalar Savaşı", "H. G. Wells", "Bilim Kurgu", 1898),
    ("Kızıl Dosya", "Arthur Conan Doyle", "Polisiye", 1887),
    ("Baskerville'lerin Köpeği", "Arthur Conan Doyle", "Polisiye", 1902),
    ("Doğu Ekspresinde Cinayet", "Agatha Christie", "Polisiye", 1934),
    ("Ve Sonra Hiç Kimse Kalmadı", "Agatha Christie", "Polisiye", 1939),
    ("Gülün Adı", "Umberto Eco", "Polisiye", 1980),
    ("Kara Kitap", "Orhan Pamuk", "Roman", 1990),
    ("Yer Demir Gök Bakır", "Yaşar Kemal", "Roman", 1963),
    ("Memleketimden İnsan Manzaraları", "Nâzım Hikmet", "Şiir", 1966),
    ("Kuvâyi Milliye", "Nâzım Hikmet", "Şiir", 1968),
    ("Garip", "Orhan Veli Kanık", "Şiir", 1941),
    ("Çile", "Necip Fazıl Kısakürek", "Şiir", 1962),
    ("Kendi Gök Kubbemiz", "Yahya Kemal Beyatlı", "Şiir", 1961),
    ("Semaver", "Sait Faik Abasıyanık", "Öykü", 1936),
    ("Alemdağ'da Var Bir Yılan", "Sait Faik Abasıyanık", "Öykü", 1954),
    ("Yalnız Efe", "Ömer Seyfettin", "Öykü", 1919),
    ("Sinekli Bakkal", "Halide Edib Adıvar", "Roman", 1936),
    ("Yaban", "Yakup Kadri Karaosmanoğlu", "Roman", 1932),
    ("Kiralık Konak", "Yakup Kadri Karaosmanoğlu", "Roman", 1922),
    ("Mai ve Siyah", "Halit Ziya Uşaklıgil", "Roman", 1897),
    ("Aşk-ı Memnu", "Halit Ziya Uşaklıgil", "Roman", 1900),
    ("Araba Sevdası", "Recaizade Mahmut Ekrem", "Roman", 1896),
    ("Nutuk", "Mustafa Kemal Atatürk", "Tarih", 1927),
    ("Osmanlı İmparatorluğu Klasik Çağ", "Halil İnalcık", "Tarih", 1973),
    ("Hayvanlardan Tanrılara: Sapiens", "Yuval Noah Harari", "Tarih", 2011),
    ("Tüfek, Mikrop ve Çelik", "Jared Diamond", "Tarih", 1997),
    ("Devlet", "Platon", "Felsefe", None),
    ("Nikomakhos'a Etik", "Aristoteles", "Felsefe", None),
    ("Böyle Buyurdu Zerdüşt", "Friedrich Nietzsche", "Felsefe", 1883),
    ("Varlık ve Zaman", "Martin Heidegger", "Felsefe", 1927),
    ("Kendime Düşünceler", "Marcus Aurelius", "Felsefe", None),
    ("Sofie'nin Dünyası", "Jostein Gaarder", "Felsefe", 1991),
    ("Prens", "Niccolò Machiavelli", "Felsefe", 1532),
    ("Kozmos", "Carl Sagan", "Bilim", 1980),
    ("Zamanın Kısa Tarihi", "Stephen Hawking", "Bilim", 1988),
    ("Gen Bencildir", "Richard Dawkins", "Bilim", 1976),
    ("Türlerin Kökeni", "Charles Darwin", "Bilim", 1859),
    ("Eminim Şaka Yapıyorsunuz Bay Feynman", "Richard Feynman", "Bilim", 1985),
    ("Sessiz Bahar", "Rachel Carson", "Bilim", 1962),
    ("İnsanın Anlam Arayışı", "Viktor Frankl", "Psikoloji", 1946),
    ("Hızlı ve Yavaş Düşünme", "Daniel Kahneman", "Psikoloji", 2011),
    ("Düşlerin Yorumu", "Sigmund Freud", "Psikoloji", 1899),
    ("Sevme Sanatı", "Erich Fromm", "Psikoloji", 1956),
    ("Akış", "Mihaly Csikszentmihalyi", "Psikoloji", 1990),
    ("Küçük Prens", "Antoine de Saint-Exupéry", "Çocuk", 1943),
    ("Alice Harikalar Diyarında", "Lewis Carroll", "Çocuk", 1865),
    ("Pinokyo", "Carlo Collodi", "Çocuk", 1883),
    ("Şeker Portakalı", "José Mauro de Vasconcelos", "Roman", 1968),
    ("Pal Sokağı Çocukları", "Ferenc Molnár", "Çocuk", 1906),
    ("Charlie'nin Çikolata Fabrikası", "Roald Dahl", "Çocuk", 1964),
    ("Matilda", "Roald Dahl", "Çocuk", 1988),
    ("Harry Potter ve Felsefe Taşı", "J. K. Rowling", "Çocuk", 1997),
    ("Hobbit", "J. R. R. Tolkien", "Roman", 1937),
    ("Yüzük Kardeşliği", "J. R. R. Tolkien", "Roman", 1954),
    ("Simyacı", "Paulo Coelho", "Roman", 1988),
    ("Martı Jonathan Livingston", "Richard Bach", "Roman", 1970),
    ("Satranç", "Stefan Zweig", "Öykü", 1942),
    ("Bilinmeyen Bir Kadının Mektubu", "Stefan Zweig", "Öykü", 1922),
]

KNOWN_ISBNS = {"Suç ve Ceza": "9789750719387"}
RETURNED_LOAN_COUNT = 30
ACTIVE_LOAN_COUNT = 8


def _slug(text: str) -> str:
    text = text.lower().replace("ı", "i")
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return ".".join(ascii_text.split())


def _isbn13(rng: random.Random) -> str:
    digits = [9, 7, 8, 9, 7, 5] + [rng.randint(0, 9) for _ in range(6)]
    check = (10 - sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits)) % 10) % 10
    return "".join(map(str, digits + [check]))


def _copies_per_book(index: int) -> int:
    # 50 kitap × 3 + 50 kitap × 2 = 250 nüsha
    return 3 if index < len(BOOKS) // 2 else 2


def run(db: Session, today: date | None = None) -> None:
    today = today or date.today()
    rng = random.Random(42)

    if db.scalar(select(User.id).limit(1)) is not None:
        raise RuntimeError(
            "Veritabanında zaten kullanıcı var; seed yalnızca boş veritabanında çalışır."
        )

    settings_service.ensure_defaults(db)
    loan_days = settings_service.get_int(db, "loan_days")

    # --- Kullanıcılar ---
    admin = User(
        email=ADMIN_LOGIN[0],
        password_hash=hash_password(ADMIN_LOGIN[1]),
        full_name="Sistem Yöneticisi",
        role=UserRole.ADMIN,
    )
    librarian_hash = hash_password(LIBRARIAN_PASSWORD)
    librarians = [
        User(
            email=f"gorevli{i}@{EMAIL_DOMAIN}",
            password_hash=librarian_hash,
            full_name=name,
            role=UserRole.LIBRARIAN,
        )
        for i, name in enumerate(LIBRARIANS, start=1)
    ]
    db.add_all([admin, *librarians])

    member_hash = hash_password(MEMBER_PASSWORD)
    member_types = [MemberType.STUDENT, MemberType.STAFF, MemberType.PUBLIC]
    members: list[Member] = []
    for i, name in enumerate(MEMBERS):
        user = User(
            email=f"{_slug(name)}@{EMAIL_DOMAIN}",
            password_hash=member_hash,
            full_name=name,
            role=UserRole.MEMBER,
        )
        start = today - timedelta(days=rng.randint(30, 700))
        member = Member(
            user=user,
            member_no=f"UYE-{i + 1:06d}",
            phone=f"05{rng.randint(30, 59)} {rng.randint(100, 999)} {rng.randint(10, 99)} "
            f"{rng.randint(10, 99)}",
            member_type=member_types[i % len(member_types)],
            membership_start=start,
            membership_end=start + timedelta(days=730),
            status=MemberStatus.ACTIVE,
        )
        members.append(member)
    db.add_all(members)

    # --- Katalog ---
    categories: dict[str, Category] = {}
    for parent_name, children in CATEGORY_TREE.items():
        parent = Category(name=parent_name)
        categories[parent_name] = parent
        for child_name in children:
            categories[child_name] = Category(name=child_name, parent=parent)
    db.add_all(categories.values())

    publishers = [Publisher(name=name) for name in PUBLISHERS]
    db.add_all(publishers)

    authors: dict[str, Author] = {}
    books: list[Book] = []
    for title, author_name, category_name, year in BOOKS:
        author = authors.setdefault(author_name, Author(full_name=author_name))
        category = categories[category_name]
        book_categories = [category]
        if category.parent is not None:
            book_categories.append(category.parent)
        book = Book(
            isbn=KNOWN_ISBNS.get(title) or _isbn13(rng),
            title=title,
            publisher=rng.choice(publishers),
            publish_year=year,
            page_count=rng.randint(90, 900),
            language="Türkçe",
            authors=[author],
            categories=book_categories,
        )
        books.append(book)
        # Kitap id'leri BOOKS sırasını izlesin (ör. "Suç ve Ceza" → 12, barkod KTP-0012-01).
        db.add(book)
        db.flush()

    category_names = list(CATEGORY_TREE)
    copies: list[BookCopy] = []
    for index, book in enumerate(books):
        top_category = book.categories[-1].name
        shelf_letter = chr(ord("A") + category_names.index(top_category))
        for n in range(1, _copies_per_book(index) + 1):
            copies.append(
                BookCopy(
                    book=book,
                    barcode=f"KTP-{book.id:04d}-{n:02d}",
                    shelf_location=f"{shelf_letter}-{rng.randint(1, 12):02d}-{rng.randint(1, 5)}",
                    status=CopyStatus.AVAILABLE,
                    acquired_at=today - timedelta(days=rng.randint(60, 1500)),
                )
            )
    db.add_all(copies)
    db.flush()

    # --- Ödünçler ---
    # Aktif ödünçler: ilki UML nesne diyagramındaki örnek (Ayşe — Suç ve Ceza).
    suc_ve_ceza_copy = next(c for c in copies if c.barcode == "KTP-0012-01")
    remaining_copies = [c for c in copies if c is not suc_ve_ceza_copy]
    rng.shuffle(remaining_copies)
    active_copies = [suc_ve_ceza_copy, *remaining_copies[: ACTIVE_LOAN_COUNT - 1]]
    returned_copies = remaining_copies[ACTIVE_LOAN_COUNT - 1 :][:RETURNED_LOAN_COUNT]

    loans: list[Loan] = []
    for member, copy in zip(members, active_copies, strict=False):
        loan_date = today - timedelta(days=7 if copy is suc_ve_ceza_copy else rng.randint(0, 10))
        loans.append(
            Loan(
                copy=copy,
                member=member,
                issued_by=rng.choice(librarians).id,
                loan_date=loan_date,
                due_date=loan_date + timedelta(days=loan_days),
                status=LoanStatus.ACTIVE,
            )
        )
        copy.status = CopyStatus.LOANED

    for copy in returned_copies:
        loan_date = today - timedelta(days=rng.randint(30, 180))
        librarian = rng.choice(librarians)
        loans.append(
            Loan(
                copy=copy,
                member=rng.choice(members),
                issued_by=librarian.id,
                loan_date=loan_date,
                due_date=loan_date + timedelta(days=loan_days),
                return_date=loan_date + timedelta(days=rng.randint(1, loan_days)),
                returned_to=librarian.id,
                status=LoanStatus.RETURNED,
            )
        )
    db.add_all(loans)
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        run(db)
        print(
            f"Seed tamamlandı: {db.query(User).count()} kullanıcı, {db.query(Book).count()} kitap, "
            f"{db.query(BookCopy).count()} nüsha, {db.query(Loan).count()} ödünç."
        )
        print(f"Admin girişi: {ADMIN_LOGIN[0]} / {ADMIN_LOGIN[1]}")


if __name__ == "__main__":
    main()
