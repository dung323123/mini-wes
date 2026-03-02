# Mini WES Database Schema

## Scope
Tài liệu này mô tả cấu trúc dữ liệu hiện tại ở mức bảng, cột, khóa và quan hệ.
Không bao gồm hướng dẫn chạy migration hay thao tác deploy.

## ER Overview
- `robots` 1 - n `missions` (qua `missions.assigned_robot_id`)
- `orders` 1 - n `missions` (qua `missions.order_id`)
- `missions` 1 - n `mission_steps`
- `robots` 1 - n `telemetry`
- `allocator_runs` 1 - n `allocator_run_items`
- `allocator_run_items` tham chiếu `orders`, `robots`, `missions`
- `events` tham chiếu tùy chọn tới `robots`, `orders`, `missions`

## Tables

### 1) `robots`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Robot id |
| name | varchar(64) | NO | UNIQUE | Tên robot |
| robot_type | varchar(32) | NO |  | `AMR`, `MANIPULATOR`, `HUMANOID`... |
| status | varchar(32) | NO |  | `IDLE`, `BUSY`, `CHARGING`, `DISABLED`, `ERROR` |
| battery_pct | int | NO |  | 0..100 |
| last_pose_x | float | NO |  | |
| last_pose_y | float | NO |  | |
| last_pose_theta | float | NO |  | |
| last_seen_at | timestamptz | NO |  | |
| created_at | timestamptz | NO |  | |
| updated_at | timestamptz | NO |  | |

### 2) `orders`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Order id |
| code | varchar(64) | NO | UNIQUE | Mã order |
| pickup_x | float | NO |  | |
| pickup_y | float | NO |  | |
| dropoff_x | float | NO |  | |
| dropoff_y | float | NO |  | |
| priority | int | NO | INDEX | 1..10 |
| status | varchar(32) | NO | INDEX | `CREATED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELED` |
| started_at | timestamptz | YES |  | |
| finished_at | timestamptz | YES |  | |
| created_at | timestamptz | NO | INDEX | |
| updated_at | timestamptz | NO |  | |

### 3) `missions`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Mission id |
| code | varchar(64) | NO | UNIQUE | Mã mission |
| mission_type | varchar(32) | NO |  | `MOVE`, `PICK`, `DOCK`, `PATROL` |
| status | varchar(32) | NO |  | `CREATED`, `ASSIGNED`, `RUNNING`, `COMPLETED`, `FAILED` |
| priority | int | NO |  | |
| order_id | UUID | YES | FK -> orders.id | Liên kết order |
| assigned_robot_id | UUID | YES | FK -> robots.id | Robot thực thi |
| progress_pct | int | NO |  | 0..100 |
| started_at | timestamptz | YES |  | |
| finished_at | timestamptz | YES |  | |
| created_at | timestamptz | NO |  | |
| updated_at | timestamptz | NO |  | |

### 4) `mission_steps`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Step id |
| mission_id | UUID | NO | FK -> missions.id | `on delete cascade` |
| seq | int | NO |  | Thứ tự step |
| action | varchar(255) | NO |  | |
| status | varchar(32) | NO |  | `PENDING`, `RUNNING`, `DONE`, `FAILED`, `SKIPPED` |
| started_at | timestamptz | YES |  | |
| finished_at | timestamptz | YES |  | |
| created_at | timestamptz | NO |  | |
| updated_at | timestamptz | NO |  | |

### 5) `telemetry`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Telemetry row id |
| robot_id | UUID | NO | FK -> robots.id | |
| x | float | NO |  | |
| y | float | NO |  | |
| theta | float | NO |  | |
| battery_pct | int | NO |  | |
| recorded_at | timestamptz | NO | INDEX | |
| created_at | timestamptz | NO |  | |

Indexes:
- `ix_telemetry_robot_recorded_at (robot_id, recorded_at)`
- `ix_telemetry_recorded_at (recorded_at)`

### 6) `events`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Event id |
| event_type | varchar(64) | NO | INDEX | Ví dụ: `MISSION_ASSIGNED`, `STEP_DONE` |
| message | text | YES |  | |
| robot_id | UUID | YES | FK -> robots.id | |
| order_id | UUID | YES | FK -> orders.id | |
| mission_id | UUID | YES | FK -> missions.id | |
| created_at | timestamptz | NO | INDEX | |

### 7) `allocator_runs`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Run id |
| status | varchar(32) | NO |  | |
| battery_min_pct | int | NO |  | |
| max_orders | int | NO |  | |
| total_orders | int | NO |  | |
| assigned_count | int | NO |  | |
| unassigned_count | int | NO |  | |
| created_at | timestamptz | NO | INDEX | |
| completed_at | timestamptz | YES |  | |

### 8) `allocator_run_items`
| Column | Type | Null | Key | Note |
|---|---|---|---|---|
| id | UUID | NO | PK | Item id |
| run_id | UUID | NO | FK -> allocator_runs.id | `on delete cascade` |
| order_id | UUID | NO | FK -> orders.id | |
| robot_id | UUID | YES | FK -> robots.id | |
| mission_id | UUID | YES | FK -> missions.id | |
| result | varchar(32) | NO | INDEX | `ASSIGNED` / `UNASSIGNED` |
| reason | varchar(255) | YES |  | |
| score | float | YES |  | |
| distance | float | YES |  | |
| created_at | timestamptz | NO |  | |

## System Table
- `alembic_version`: trạng thái version migration.
