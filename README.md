# Mini WES - Project Overview

## 1) Mục tiêu nghiệp vụ
Mini WES là hệ thống mô phỏng orchestration cho đội robot trong kho, tập trung vào các luồng cốt lõi:
- tiếp nhận order vận chuyển nội bộ,
- tạo và theo dõi task/misson thực thi,
- phân bổ robot theo trạng thái + battery + khoảng cách,
- ghi nhận telemetry và event log để giám sát vận hành.

## 2) Năng lực hệ thống hiện tại

### Fleet Monitoring
- Theo dõi trạng thái robot toàn fleet (`IDLE/BUSY/CHARGING/DISABLED/ERROR`).
- Quan sát pose/battery gần nhất.
- Hiển thị task active của từng robot.

### Robot Management
- Đăng ký robot mới.
- Bật/tắt robot.
- Xem robot detail + mission đang active (nếu có).

### Order & Task Lifecycle
- Tạo order pickup/dropoff với priority.
- Quản lý trạng thái order.
- Mapping `task ~= mission` để theo dõi tiến độ thực thi.

### Allocation
- Chạy allocator chủ động (`Run Allocation`).
- Chọn robot đủ điều kiện (idle + battery threshold).
- Tính điểm theo distance, priority, battery.
- Tạo mission và gán robot.
- Lưu lịch sử từng đợt phân bổ.

### Telemetry & Events
- Ingest telemetry thủ công và telemetry phát sinh từ simulator.
- Query latest/time-range/export CSV.
- Ghi event timeline cho các mốc nghiệp vụ chính.

## 3) Kiến trúc kỹ thuật

### Backend
- Framework: FastAPI
- ORM: SQLAlchemy 2.x
- Migration: Alembic
- DB: PostgreSQL (local Docker / Supabase cloud)
- App shape: Router-driven REST API + service layer cho simulator/event logging.

### Frontend
- Framework: React + Vite
- Vai trò: dashboard thao tác nhanh cho demo nghiệp vụ, gọi trực tiếp REST API.

### Infra / Deploy
- Backend deploy trên Render.
- Database cloud trên Supabase.
- Frontend deploy trên Vercel.

## 4) Domain Model (mức nghiệp vụ)
- `Robot`: tài nguyên thực thi.
- `Order`: yêu cầu vận hành vào hệ thống.
- `Mission` + `MissionStep`: kế hoạch và tiến trình thực thi.
- `AllocatorRun` + `AllocatorRunItem`: log quyết định phân bổ.
- `Telemetry`: dữ liệu time-series vận hành robot.
- `Event`: nhật ký sự kiện nghiệp vụ.

## 5) Luồng điển hình end-to-end
1. Tạo `Order` với pickup/dropoff.
2. Chạy allocator.
3. Hệ thống gán `Robot` phù hợp và tạo `Mission`.
4. Simulator đẩy mission qua các trạng thái chạy step.
5. Telemetry và events được ghi liên tục.
6. Dashboard phản ánh trạng thái fleet/order/task gần thời gian thực.

## 6) Định hướng mở rộng
- Thêm auth + multi-tenant workspace.
- Hardening allocator (ràng buộc vùng, năng lực robot, SLA).
- Tối ưu truy vấn telemetry/events ở quy mô lớn.
- Bổ sung test integration và contract test cho API công khai.
