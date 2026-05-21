# Trading Bot

AI-powered crypto trading bot dengan FastAPI + React.

## Cara menjalankan

### 1. Clone & setup environment

```bash
git clone <repo-url>
cd trading-bot

cp .env.example .env
# Edit .env dan isi API key + database URL
```

### 2. Jalankan database (Docker)

```bash
# PostgreSQL + Redis
docker compose up -d

# Cek status
docker compose ps
```

### 3. Jalankan backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Jalankan server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Server berjalan di: http://localhost:8000
Swagger docs: http://localhost:8000/docs

### 4. Jalankan frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend berjalan di: http://localhost:5173

---

## Endpoints utama

| Method | URL              | Keterangan         |
| ------ | ---------------- | ------------------ |
| GET    | /api/health      | Health check       |
| GET    | /api/bot/status  | Status bot         |
| POST   | /api/bot/start   | Mulai bot          |
| POST   | /api/bot/stop    | Hentikan bot       |
| GET    | /api/trades      | Riwayat trade      |
| GET    | /api/signals     | Sinyal AI          |
| GET    | /api/performance | Statistik performa |
| WS     | /ws/live         | Live data stream   |
