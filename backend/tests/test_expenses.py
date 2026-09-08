def test_create_expense(client, demo_user, auth_headers):
    response = client.post(
        "/expenses",
        json={
            "amount": 12.50,
            "category": "food",
            "note": "Lunch",
        },
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 12.50
    assert data["category"] == "food"
    assert data["note"] == "Lunch"


def test_get_expenses(client, demo_user, auth_headers):
    client.post(
        "/expenses",
        json={"amount": 25.00, "category": "transport"},
        **auth_headers,
    )
    response = client.get("/expenses", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "expenses" in data
    assert "monthly_budget" in data
    assert len(data["expenses"]) >= 1


def test_update_expense(client, demo_user, auth_headers):
    create = client.post(
        "/expenses",
        json={"amount": 10.00, "category": "other"},
        **auth_headers,
    )
    expense_id = create.json()["id"]

    response = client.patch(
        f"/expenses/{expense_id}",
        json={"note": "Updated note"},
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["note"] == "Updated note"


def test_delete_expense(client, demo_user, auth_headers):
    create = client.post(
        "/expenses",
        json={"amount": 5.00, "category": "food"},
        **auth_headers,
    )
    expense_id = create.json()["id"]

    response = client.delete(f"/expenses/{expense_id}", **auth_headers)
    assert response.status_code == 200

    response = client.get("/expenses", **auth_headers)
    ids = [e["id"] for e in response.json()["expenses"]]
    assert expense_id not in ids


def test_delete_nonexistent_expense(client, demo_user, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/expenses/{fake_id}", **auth_headers)
    assert response.status_code == 404
