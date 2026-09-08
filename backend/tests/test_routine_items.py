def test_add_item_to_routine(client, demo_user, auth_headers):
    routine = client.post(
        "/routines", json={"name": "Push Day"}, **auth_headers
    ).json()

    response = client.post(
        f"/routines/{routine['id']}/items",
        json={
            "exercise_name": "Bench Press",
            "sets": 4,
            "reps": 8,
            "day_of_week": "monday",
        },
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["exercise_name"] == "Bench Press"
    assert data["sets"] == 4
    assert data["reps"] == 8


def test_add_item_to_nonexistent_routine(client, demo_user, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/routines/{fake_id}/items",
        json={"exercise_name": "Press"},
        **auth_headers,
    )
    assert response.status_code == 404


def test_delete_routine_item(client, demo_user, auth_headers):
    routine = client.post(
        "/routines", json={"name": "Leg Day"}, **auth_headers
    ).json()
    item = client.post(
        f"/routines/{routine['id']}/items",
        json={"exercise_name": "Squats", "sets": 5, "reps": 5},
        **auth_headers,
    ).json()

    response = client.delete(
        f"/routines/{routine['id']}/items/{item['id']}",
        **auth_headers,
    )
    assert response.status_code == 200

    # Verify item is gone
    get_resp = client.get(f"/routines/{routine['id']}", **auth_headers)
    items = get_resp.json()["items"]
    assert item["id"] not in [i["id"] for i in items]


def test_delete_nonexistent_item(client, demo_user, auth_headers):
    routine = client.post(
        "/routines", json={"name": "Empty"} , **auth_headers
    ).json()
    fake_item = "00000000-0000-0000-0000-000000000000"
    response = client.delete(
        f"/routines/{routine['id']}/items/{fake_item}",
        **auth_headers,
    )
    assert response.status_code == 404
