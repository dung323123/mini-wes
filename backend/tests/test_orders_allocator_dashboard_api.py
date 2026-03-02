def test_order_allocator_and_dashboard_flow(client, unique_suffix):
    for i in range(2):
        created = client.post(
            "/robots",
            json={
                "name": f"AMR-A-{unique_suffix}-{i}",
                "robot_type": "AMR",
                "status": "IDLE",
                "battery_pct": 98,
            },
        )
        assert created.status_code == 201

    order_resp = client.post(
        "/orders",
        json={
            "code": f"ORD-T-{unique_suffix}",
            "pickup_location": {"x": 1.0, "y": 1.0},
            "dropoff_location": {"x": 5.0, "y": 5.0},
            "priority": 7,
        },
    )
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    alloc = client.post("/allocator/run", json={"max_orders": 5, "battery_min_pct": 20})
    assert alloc.status_code == 200
    payload = alloc.json()
    assert payload["summary"]["total"] >= 1
    assert payload["summary"]["assigned"] >= 1

    tasks = client.get("/tasks")
    assert tasks.status_code == 200
    assert any(t["order_id"] == order_id for t in tasks.json())

    dashboard = client.get("/dashboard/summary")
    assert dashboard.status_code == 200
    summary = dashboard.json()
    assert "robots_total" in summary
    assert "tasks_running" in summary
