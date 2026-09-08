from datetime import datetime, timezone, timedelta


def test_create_workout(client, demo_user, auth_headers):
    response = client.post(
        "/workouts",
        json={
            "type": "Run",
            "duration_mins": 30,
            "notes": "Morning run",
        },
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "Run"
    assert data["duration_mins"] == 30


def test_get_workouts(client, demo_user, auth_headers):
    client.post(
        "/workouts",
        json={"type": "Gym", "duration_mins": 45},
        **auth_headers,
    )
    response = client.get("/workouts", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_delete_workout(client, demo_user, auth_headers):
    create = client.post(
        "/workouts",
        json={"type": "Yoga", "duration_mins": 20},
        **auth_headers,
    )
    workout_id = create.json()["id"]

    response = client.delete(f"/workouts/{workout_id}", **auth_headers)
    assert response.status_code == 200

    response = client.get("/workouts", **auth_headers)
    ids = [w["id"] for w in response.json()]
    assert workout_id not in ids


def test_delete_nonexistent_workout(client, demo_user, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/workouts/{fake_id}", **auth_headers)
    assert response.status_code == 404
