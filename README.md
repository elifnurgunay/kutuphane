# Kütüphane Otomasyon Sistemi

Kitap, üye, ödünç, iade, rezervasyon ve gecikme cezası süreçlerini yöneten web uygulaması.

**Yığın:** FastAPI + SQLAlchemy + PostgreSQL · React + Vite + TypeScript + Tailwind

## Docker ile çalıştırma

```bash
cp .env.example .env
docker compose up --build
```

| Servis | Adres |
|---|---|
| Arayüz | http://localhost:8080 |
| API | http://localhost:8000 (Swagger: `/docs`, sağlık: `/health`) |
| PostgreSQL | localhost:5432 (`kutuphane_db`) |

## Yerel geliştirme

### Backend (Python 3.12)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload # http://localhost:8000
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
