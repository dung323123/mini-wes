def test_mission_create_and_get_detail(client, unique_suffix):
    robot = client.post(
        "/robots",
        json={
            "name": f"AMR-M-{unique_suffix}",
            "robot_type": "AMR",
            "status": "IDLE",
            "battery_pct": 95,
        },
    ).json()

    mission_create = client.post(
        "/missions",
        json={
            "mission_type": "MOVE",
            "priority": 5,
            "steps": [
                {"seq": 1, "action": "PICKUP"},
                {"seq": 2, "action": "DROPOFF"},
            ],
        },
    )
    assert mission_create.status_code == 201
    mission = mission_create.json()
    mission_id = mission["id"]
    assert mission["status"] == "CREATED"
    assert len(mission["steps"]) == 2

    mission_detail = client.get(f"/missions/{mission_id}")
    assert mission_detail.status_code == 200
    assert mission_detail.json()["id"] == mission_id

    assigned = client.post(f"/missions/{mission_id}/assign", json={"robot_id": robot["id"]})
    assert assigned.status_code == 200
    assigned_body = assigned.json()
    # Simulator is monkeypatched in tests, so status remains ASSIGNED.
    assert assigned_body["status"] == "ASSIGNED"
    assert assigned_body["assigned_robot_id"] == robot["id"]
