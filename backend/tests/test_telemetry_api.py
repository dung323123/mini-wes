def test_telemetry_ingest_and_latest(client, unique_suffix):
    robot_resp = client.post(
        "/robots",
        json={
            "name": f"AMR-TEL-{unique_suffix}",
            "robot_type": "AMR",
            "status": "IDLE",
            "battery_pct": 80,
        },
    )
    assert robot_resp.status_code == 201
    robot_id = robot_resp.json()["id"]

    ingest = client.post(
        "/telemetry/ingest",
        json={
            "robot_id": robot_id,
            "x": 12.3,
            "y": 4.5,
            "theta": 0.2,
            "battery_pct": 79,
        },
    )
    assert ingest.status_code == 201
    assert ingest.json()["robot_id"] == robot_id

    latest = client.get("/telemetry/latest", params={"robot_id": robot_id})
    assert latest.status_code == 200
    rows = latest.json()
    assert len(rows) == 1
    assert rows[0]["robot_id"] == robot_id
