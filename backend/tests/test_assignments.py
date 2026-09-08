from datetime import datetime, timezone, timedelta


def test_create_assignment(client, demo_user, auth_headers):
    response = client.post(
        "/assignments",
        json={
            "title": "CS Final Project",
            "course": "CS320",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "estimated_hours": 10,
        },
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "CS Final Project"
    assert data["course"] == "CS320"
    assert data["estimated_hours"] == 10.0
    assert data["status"] == "pending"


def test_get_assignments(client, demo_user, auth_headers):
    # Create one first
    client.post(
        "/assignments",
        json={
            "title": "Test HW",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        },
        **auth_headers,
    )
    response = client.get("/assignments", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(a["title"] == "Test HW" for a in data)


def test_update_assignment_status(client, demo_user, auth_headers):
    create = client.post(
        "/assignments",
        json={
            "title": "To Complete",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        },
        **auth_headers,
    )
    assignment_id = create.json()["id"]

    response = client.patch(
        f"/assignments/{assignment_id}",
        json={"status": "done"},
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_delete_assignment(client, demo_user, auth_headers):
    create = client.post(
        "/assignments",
        json={
            "title": "To Delete",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
        **auth_headers,
    )
    assignment_id = create.json()["id"]

    response = client.delete(f"/assignments/{assignment_id}", **auth_headers)
    assert response.status_code == 200

    # Should not appear in list (soft deleted)
    response = client.get("/assignments", **auth_headers)
    ids = [a["id"] for a in response.json()]
    assert assignment_id not in ids


def test_delete_nonexistent_assignment(client, demo_user, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/assignments/{fake_id}", **auth_headers)
    assert response.status_code == 404
