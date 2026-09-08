def test_create_routine(client, demo_user, auth_headers):
    response = client.post(
        "/routines",
        json={
            "name": "Push Pull Legs",
            "items": [
                {
                    "exercise_name": "Bench Press",
                    "sets": 4,
                    "reps": 8,
                    "day_of_week": "monday",
                    "order_index": 0,
                },
                {
                    "exercise_name": "Overhead Press",
                    "sets": 3,
                    "reps": 10,
                    "day_of_week": "monday",
                    "order_index": 1,
                },
            ],
        },
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Push Pull Legs"
    assert len(data["items"]) == 2
    assert data["items"][0]["exercise_name"] == "Bench Press"


def test_create_routine_no_items(client, demo_user, auth_headers):
    response = client.post(
        "/routines",
        json={"name": "Simple Routine"},
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Simple Routine"
    assert response.json()["items"] == []


def test_get_routines(client, demo_user, auth_headers):
    client.post("/routines", json={"name": "A"}, **auth_headers)
    client.post("/routines", json={"name": "B"}, **auth_headers)

    response = client.get("/routines", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_routine_by_id(client, demo_user, auth_headers):
    create = client.post(
        "/routines",
        json={"name": "Fetch Me"},
        **auth_headers,
    )
    routine_id = create.json()["id"]

    response = client.get(f"/routines/{routine_id}", **auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Fetch Me"


def test_get_routine_not_found(client, demo_user, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/routines/{fake_id}", **auth_headers)
    assert response.status_code == 404


def test_update_routine(client, demo_user, auth_headers):
    create = client.post("/routines", json={"name": "Old"}, **auth_headers)
    routine_id = create.json()["id"]

    response = client.patch(
        f"/routines/{routine_id}",
        json={"name": "New"},
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_delete_routine(client, demo_user, auth_headers):
    create = client.post("/routines", json={"name": "Doomed"}, **auth_headers)
    routine_id = create.json()["id"]

    response = client.delete(f"/routines/{routine_id}", **auth_headers)
    assert response.status_code == 200

    response = client.get("/routines", **auth_headers)
    ids = [r["id"] for r in response.json()]
    assert routine_id not in ids


def test_delete_nonexistent_routine(client, demo_user, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/routines/{fake_id}", **auth_headers)
    assert response.status_code == 404


def test_routine_isolation(client, demo_user, auth_headers):
    create = client.post("/routines", json={"name": "Mine"}, **auth_headers)
    routine_id = create.json()["id"]

    # Create another user
    client.post(
        "/auth/register",
        json={"email": "other@lifeos.app", "password": "pass1234", "name": "Other"},
    )
    login = client.post(
        "/auth/login",
        json={"email": "other@lifeos.app", "password": "pass1234"},
    )
    other_token = login.json().get("user", {}).get("id")

    # Other user shouldn't see our routine
    from app.services.auth import create_access_token
    other_headers = {"cookies": {"access_token": create_access_token({"sub": other_token})}}

    response = client.get("/routines", **other_headers)
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()]
    assert routine_id not in ids
