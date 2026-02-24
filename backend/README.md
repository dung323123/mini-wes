# Mini WES Backend (FastAPI + PostgreSQL)

## 1) Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2) Start PostgreSQL (Docker)

```bash
cd backend
docker compose up -d
docker compose ps
```

Postgres runs at `localhost:5432` with:
- db: `miniwes`
- user: `postgres`
- password: `postgres`

## 3) Run migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

This creates:
- `robots`
- `missions`
- `mission_steps`

## 4) Seed demo data (optional)

```bash
cd backend
source .venv/bin/activate
python -m app.seed.seed
```

## 5) Run API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Available APIs

- `POST /robots`
- `GET /robots?status=&type=&enabled=`
- `GET /robots/{id}` (`include_mission=true|false`)
- `PATCH /robots/{id}`
- `GET /missions?status=&robot_id=`
- `GET /missions/{id}`
- `POST /missions`
- `POST /missions/{id}/assign`
