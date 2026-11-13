from app.models.activity_log import ActivityLog


def test_onboarding_started_is_logged(client, demo_user, auth_headers, db_session):
    response = client.post("/onboarding/events", json={"event": "onboarding_started"}, **auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "onboarding_started"
    assert body["entity_type"] == "onboarding"
    assert body["details"] is None
    assert "id" in body and "created_at" in body

    rows = db_session.query(ActivityLog).filter(ActivityLog.user_id == demo_user.id).all()
    assert len(rows) == 1
    assert rows[0].action == "onboarding_started"
    assert rows[0].entity_type == "onboarding"
    assert rows[0].details is None


def test_step_completed_requires_step(client, demo_user, auth_headers):
    response = client.post("/onboarding/events", json={"event": "onboarding_step_completed"}, **auth_headers)
    assert response.status_code == 400
    assert "step is required" in response.json()["detail"]


def test_step_completed_rejects_out_of_range_step(client, demo_user, auth_headers):
    response = client.post(
        "/onboarding/events",
        json={"event": "onboarding_step_completed", "step": 9},
        **auth_headers,
    )
    assert response.status_code == 400
    assert "step must be between 1 and 4" in response.json()["detail"]


def test_step_completed_logs_step_in_details(client, demo_user, auth_headers, db_session):
    response = client.post(
        "/onboarding/events",
        json={"event": "onboarding_step_completed", "step": 2},
        **auth_headers,
    )
    assert response.status_code == 200

    row = db_session.query(ActivityLog).filter(ActivityLog.user_id == demo_user.id).one()
    assert row.action == "onboarding_step_completed"
    assert row.details == "step=2"


def test_unknown_event_is_rejected(client, demo_user, auth_headers):
    response = client.post("/onboarding/events", json={"event": "bogus_event"}, **auth_headers)
    assert response.status_code == 422


def test_onboarding_completed_sets_timestamp_once(client, demo_user, auth_headers, db_session):
    assert demo_user.onboarding_completed_at is None

    response = client.post("/onboarding/events", json={"event": "onboarding_completed"}, **auth_headers)
    assert response.status_code == 200
    db_session.refresh(demo_user)
    first_ts = demo_user.onboarding_completed_at
    assert first_ts is not None

    # Idempotent: a repeat call never moves the timestamp.
    response = client.post("/onboarding/events", json={"event": "onboarding_completed"}, **auth_headers)
    assert response.status_code == 200
    db_session.refresh(demo_user)
    assert demo_user.onboarding_completed_at == first_ts

    rows = db_session.query(ActivityLog).filter(ActivityLog.user_id == demo_user.id).all()
    assert len(rows) == 2
    assert all(r.action == "onboarding_completed" for r in rows)


def test_requires_auth(client):
    response = client.post("/onboarding/events", json={"event": "onboarding_started"})
    assert response.status_code == 401
