from datetime import date, timedelta


def test_create_job(client, demo_user, auth_headers):
    response = client.post(
        "/jobs",
        json={
            "company": "Google",
            "role": "SWE Intern",
            "applied_date": date.today().isoformat(),
        },
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Google"
    assert data["role"] == "SWE Intern"
    assert data["status"] == "applied"


def test_get_jobs(client, demo_user, auth_headers):
    client.post(
        "/jobs",
        json={
            "company": "Meta",
            "role": "Backend Intern",
            "applied_date": date.today().isoformat(),
        },
        **auth_headers,
    )
    response = client.get("/jobs", **auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_job_by_id(client, demo_user, auth_headers):
    create = client.post(
        "/jobs",
        json={
            "company": "Apple",
            "role": "ML Intern",
            "applied_date": date.today().isoformat(),
        },
        **auth_headers,
    )
    job_id = create.json()["id"]

    response = client.get(f"/jobs/{job_id}", **auth_headers)
    assert response.status_code == 200
    assert response.json()["company"] == "Apple"


def test_update_job_status(client, demo_user, auth_headers):
    create = client.post(
        "/jobs",
        json={
            "company": "Amazon",
            "role": "SDE",
            "applied_date": date.today().isoformat(),
        },
        **auth_headers,
    )
    job_id = create.json()["id"]

    response = client.patch(
        f"/jobs/{job_id}",
        json={"status": "oa"},
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "oa"


def test_delete_job(client, demo_user, auth_headers):
    create = client.post(
        "/jobs",
        json={
            "company": "Startup",
            "role": "Intern",
            "applied_date": date.today().isoformat(),
        },
        **auth_headers,
    )
    job_id = create.json()["id"]

    response = client.delete(f"/jobs/{job_id}", **auth_headers)
    assert response.status_code == 200


def test_delete_nonexistent_job(client, demo_user, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/jobs/{fake_id}", **auth_headers)
    assert response.status_code == 404
