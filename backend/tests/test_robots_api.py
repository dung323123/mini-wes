def test_robot_create_detail_enable_disable(client, unique_suffix):
    payload = {
        "name": f"AMR-T-{unique_suffix}",
        "robot_type": "AMR",
        "status": "IDLE",
        "battery_pct": 90,
    }

    created = client.post("/robots", json=payload)
    assert created.status_code == 201
    robot = created.json()
    robot_id = robot["id"]
    assert robot["name"] == payload["name"]
    assert robot["status"] == "IDLE"

    listed = client.get("/robots")
    assert listed.status_code == 200
    assert any(x["id"] == robot_id for x in listed.json())

    detail = client.get(f"/robots/{robot_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == robot_id

    disabled = client.patch(f"/robots/{robot_id}", json={"enabled": False})
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"

    only_disabled = client.get("/robots", params={"enabled": "false"})
    assert only_disabled.status_code == 200
    assert any(x["id"] == robot_id for x in only_disabled.json())

    enabled = client.patch(f"/robots/{robot_id}", json={"enabled": True})
    assert enabled.status_code == 200
    assert enabled.json()["status"] == "IDLE"
