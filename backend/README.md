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

Seed mặc định sẽ `reset` dữ liệu hiện có rồi tạo fake data đầy đủ cho:
- robots
- orders
- missions + mission_steps
- telemetry
- events

Nếu muốn giữ dữ liệu cũ và chỉ thêm:

```bash
python -m app.seed.seed --no-reset
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

## 6) Deploy FastAPI (Render)

Repo đã có sẵn:
- `render.yaml` (ở root project)
- `backend/start.sh` (run migration + start uvicorn)

Các bước:
1. Push code lên GitHub.
2. Vào Render -> `New` -> `Blueprint` -> chọn repo.
3. Render sẽ đọc `render.yaml` và tạo service `mini-wes-backend`.
4. Trong service, set env var:
- `DATABASE_URL`: connection string Supabase (dạng `postgresql+psycopg2://...?...sslmode=require`)
- `CORS_ORIGINS`: domain frontend, ví dụ `https://your-frontend.vercel.app`
5. Deploy và kiểm tra:
- `https://<render-service>/health`
- `https://<render-service>/docs`

## 7) Testing (pytest)

Tạo DB test riêng và set env trước khi chạy (không dùng production DB):

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
export TEST_DATABASE_URL='postgresql+psycopg2://<user>:<pass>@<host>:5432/<db>?sslmode=require'
pytest -q
```

Bộ test hiện tại kiểm tra:
- health
- robots CRUD cơ bản (create/detail/enable/disable)
- missions create + assign
- orders + allocator + dashboard flow
- telemetry ingest + latest

## Available APIs

- `POST /robots`
- `GET /robots?status=&type=&enabled=`
- `GET /robots/{id}` (`include_mission=true|false`)
- `PATCH /robots/{id}`
- `GET /missions?status=&robot_id=`
- `GET /missions/{id}`
- `POST /missions`
- `POST /missions/{id}/assign`
- `POST /orders`
- `GET /orders?status=&priority=`
- `GET /orders/{id}`
- `PATCH /orders/{id}`
- `GET /tasks?status=&robot_id=&order_id=`
- `GET /tasks/{id}`
- `POST /allocator/run`
- `GET /allocator/runs/{id}`
- `POST /telemetry/ingest`
- `GET /telemetry/latest?robot_id=`
- `GET /telemetry?robot_id=&from=&to=&limit=`
- `GET /telemetry/export.csv?robot_id=&from=&to=`
- `GET /events?type=&robot_id=&order_id=&mission_id=&from=&to=&limit=`
- `GET /dashboard/summary`
- `GET /dashboard/fleet`
