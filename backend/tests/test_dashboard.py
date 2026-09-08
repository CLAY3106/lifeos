from datetime import datetime, timezone, timedelta


def test_dashboard_authenticated(client, demo_user, auth_headers):
    response = client.get("/dashboard", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert "assignments" in data
    assert "jobs" in data
    assert "fitness" in data
    assert "finance" in data
    assert data["user"]["email"] == "test@lifeos.app"


def test_dashboard_unauthenticated(client):
    response = client.get("/dashboard")
    assert response.status_code == 401


def test_dashboard_with_data(client, demo_user, auth_headers):
    # Create some data
    client.post(
        "/assignments",
        json={
            "title": "Dashboard HW",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "estimated_hours": 5,
        },
        **auth_headers,
    )
    client.post(
        "/workouts",
        json={"type": "Run", "duration_mins": 30},
        **auth_headers,
    )
    client.post(
        "/expenses",
        json={"amount": 20.00, "category": "food"},
        **auth_headers,
    )

    response = client.get("/dashboard", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["assignments"]["weekly_load_hours"] >= 5
    assert data["finance"]["total_spent"] >= 20.00


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
