# Kütüphane Otomasyon Sistemi

Kitap, üye, ödünç, iade, rezervasyon ve gecikme cezası süreçlerini yöneten web uygulaması.

**Yığın:** FastAPI + SQLAlchemy + PostgreSQL · React + Vite + TypeScript + Tailwind

## Docker ile çalıştırma

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python -m app.seed   # örnek veri (yalnızca ilk kez)
```

Backend konteyneri açılışta `alembic upgrade head` çalıştırır. Veritabanı Türkçe sıralamayla
(ICU `tr-TR`) oluşturulur; bu ayar yalnızca volume ilk oluşturulurken uygulanır, değiştirmek için
`docker compose down -v` ile volume silinmelidir (veriler gider).

| Servis | Adres |
|---|---|
| Arayüz | http://localhost:8080 |
| API | http://localhost:8000 (Swagger: `/docs`, sağlık: `/health`) |
| PostgreSQL | localhost:5433 (`kutuphane_db`) |

## Yerel geliştirme

### Backend (Python 3.12)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head          # şemayı ve varsayılan ayarları oluşturur (SQLite: kutuphane.db)
python -m app.seed            # örnek veri: 1 admin, 2 görevli, 20 üye, 100 kitap, 250 nüsha
uvicorn app.main:app --reload # http://localhost:8000
```

Eşzamanlılık testini gerçek PostgreSQL satır kilidiyle de çalıştırmak için
Docker'daki veritabanında `kutuphane_test` adlı boş bir veritabanı oluşturup:

```bash
TEST_POSTGRES_URL=postgresql+psycopg://kutuphane:kutuphane@localhost:5433/kutuphane_test pytest tests/unit/test_loan_concurrency.py
```

Model değişince yeni migration:

```bash
alembic revision --autogenerate -m "aciklama"
```

Test ve lint:

```bash
pytest
ruff check .
ruff format .
```

### Frontend (Node 22)

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173, /api → localhost:8000
```

Test, lint ve format:

```bash
npm test
npm run lint
npm run format
npm run build
```

## Varsayılan giriş bilgileri (seed)

Yalnızca geliştirme içindir.

| Rol | E-posta | Şifre |
|---|---|---|
| Yönetici | admin@kutuphane.local | Admin123! |
| Görevli | gorevli1@kutuphane.local, gorevli2@kutuphane.local | Gorevli123! |
| Üye | ayse.yilmaz@kutuphane.local (ve diğer 19 üye, `ad.soyad@kutuphane.local`) | Uye12345! |
