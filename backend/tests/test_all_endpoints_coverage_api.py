from datetime import datetime, timedelta, timezone


def _create_robot(client, name: str, robot_type: str = "AMR", status: str = "IDLE", battery_pct: int = 90):
    r = client.post(
        "/robots",
        json={
            "name": name,
            "robot_type": robot_type,
            "status": status,
            "battery_pct": battery_pct,
        },
    )
    assert r.status_code == 201
    return r.json()


def _create_order(client, code: str, priority: int = 5):
    r = client.post(
        "/orders",
        json={
            "code": code,
            "pickup_location": {"x": 1.0, "y": 2.0},
            "dropoff_location": {"x": 5.0, "y": 7.0},
            "priority": priority,
        },
    )
    assert r.status_code == 201
    return r.json()


def _create_mission(client, mission_type: str = "MOVE", priority: int = 5, order_id=None):
    payload = {
        "mission_type": mission_type,
        "priority": priority,
        "steps": [
            {"seq": 1, "action": "PICKUP"},
            {"seq": 2, "action": "DROPOFF"},
        ],
    }
    if order_id:
        payload["order_id"] = order_id
    r = client.post("/missions", json=payload)
    assert r.status_code == 201
    return r.json()


def test_all_list_and_summary_endpoints_on_empty_state(client):
    assert client.get("/health").status_code == 200
    assert client.get("/robots").status_code == 200
    assert client.get("/orders").status_code == 200
    assert client.get("/missions").status_code == 200
    assert client.get("/tasks").status_code == 200
    assert client.get("/events").status_code == 200
    assert client.get("/telemetry").status_code == 200
    assert client.get("/telemetry/latest").status_code == 200

    summary = client.get("/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["robots_total"] == 0

    fleet = client.get("/dashboard/fleet")
    assert fleet.status_code == 200
    assert fleet.json() == []


def test_all_resource_endpoints_and_filters(client, unique_suffix):
    robot_idle = _create_robot(client, f"AMR-COV-{unique_suffix}-1", status="IDLE", battery_pct=95)
    robot_disabled = _create_robot(client, f"AMR-COV-{unique_suffix}-2", status="DISABLED", battery_pct=40)

    robots_idle = client.get("/robots", params={"status": "IDLE", "type": "AMR", "enabled": "true"})
    assert robots_idle.status_code == 200
    assert any(r["id"] == robot_idle["id"] for r in robots_idle.json())

    robots_disabled = client.get("/robots", params={"enabled": "false"})
    assert robots_disabled.status_code == 200
    assert any(r["id"] == robot_disabled["id"] for r in robots_disabled.json())

    robot_detail = client.get(f"/robots/{robot_idle['id']}", params={"include_mission": "false"})
    assert robot_detail.status_code == 200
    assert robot_detail.json()["id"] == robot_idle["id"]

    patch_ok = client.patch(f"/robots/{robot_idle['id']}", json={"battery_pct": 88, "last_pose_x": 3.3})
    assert patch_ok.status_code == 200
    assert patch_ok.json()["battery_pct"] == 88

    order_created = _create_order(client, f"ORD-COV-{unique_suffix}-1", priority=8)
    order_created_2 = _create_order(client, f"ORD-COV-{unique_suffix}-2", priority=2)

    order_detail = client.get(f"/orders/{order_created['id']}")
    assert order_detail.status_code == 200
    assert order_detail.json()["id"] == order_created["id"]

    order_list_filtered = client.get("/orders", params={"status": "CREATED", "priority": 8})
    assert order_list_filtered.status_code == 200
    assert any(o["id"] == order_created["id"] for o in order_list_filtered.json())

    order_patch = client.patch(f"/orders/{order_created_2['id']}", json={"status": "CANCELED"})
    assert order_patch.status_code == 200
    assert order_patch.json()["status"] == "CANCELED"

    mission = _create_mission(client, order_id=order_created["id"])
    mission_detail = client.get(f"/missions/{mission['id']}")
    assert mission_detail.status_code == 200
    assert mission_detail.json()["id"] == mission["id"]

    mission_assign = client.post(f"/missions/{mission['id']}/assign", json={"robot_id": robot_idle["id"]})
    assert mission_assign.status_code == 200
    assert mission_assign.json()["status"] == "ASSIGNED"

    mission_list_filtered = client.get("/missions", params={"status": "ASSIGNED", "robot_id": robot_idle["id"]})
    assert mission_list_filtered.status_code == 200
    assert any(m["id"] == mission["id"] for m in mission_list_filtered.json())

    tasks = client.get("/tasks", params={"status": "ASSIGNED", "robot_id": robot_idle["id"], "order_id": order_created["id"]})
    assert tasks.status_code == 200
    assert any(t["id"] == mission["id"] for t in tasks.json())

    task_detail = client.get(f"/tasks/{mission['id']}")
    assert task_detail.status_code == 200
    assert task_detail.json()["id"] == mission["id"]

    telemetry_ingest = client.post(
        "/telemetry/ingest",
        json={
            "robot_id": robot_idle["id"],
            "x": 10.1,
            "y": 11.2,
            "theta": 0.3,
            "battery_pct": 87,
        },
    )
    assert telemetry_ingest.status_code == 201

    now = datetime.now(timezone.utc)
    from_ts = (now - timedelta(days=1)).isoformat()
    to_ts = (now + timedelta(days=1)).isoformat()

    telemetry_latest_by_robot = client.get("/telemetry/latest", params={"robot_id": robot_idle["id"]})
    assert telemetry_latest_by_robot.status_code == 200
    assert len(telemetry_latest_by_robot.json()) == 1

    telemetry_list = client.get(
        "/telemetry",
        params={"robot_id": robot_idle["id"], "from": from_ts, "to": to_ts, "limit": 50},
    )
    assert telemetry_list.status_code == 200
    assert len(telemetry_list.json()) >= 1

    telemetry_csv = client.get("/telemetry/export.csv", params={"robot_id": robot_idle["id"], "from": from_ts, "to": to_ts})
    assert telemetry_csv.status_code == 200
    assert "text/csv" in telemetry_csv.headers.get("content-type", "")
    assert "robot_id" in telemetry_csv.text

    alloc_run = client.post("/allocator/run", json={"max_orders": 10, "battery_min_pct": 20})
    assert alloc_run.status_code == 200
    run_id = alloc_run.json()["run_id"]

    alloc_run_detail = client.get(f"/allocator/runs/{run_id}")
    assert alloc_run_detail.status_code == 200
    assert alloc_run_detail.json()["id"] == run_id

    events_all = client.get("/events", params={"limit": 500})
    assert events_all.status_code == 200
    assert len(events_all.json()) > 0

    events_filtered = client.get(
        "/events",
        params={
            "type": "MISSION_ASSIGNED",
            "robot_id": robot_idle["id"],
            "order_id": order_created["id"],
            "mission_id": mission["id"],
            "from": from_ts,
            "to": to_ts,
            "limit": 200,
        },
    )
    assert events_filtered.status_code == 200

    dashboard_summary = client.get("/dashboard/summary")
    assert dashboard_summary.status_code == 200
    assert dashboard_summary.json()["robots_total"] >= 2

    dashboard_fleet = client.get("/dashboard/fleet")
    assert dashboard_fleet.status_code == 200
    assert any(r["robot_id"] == robot_idle["id"] for r in dashboard_fleet.json())
