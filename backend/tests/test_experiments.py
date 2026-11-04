"""
A/B Testing Tests — Assignment, Exposure, Events, and Results

The properties that matter:

1. Assignment is deterministic and stable across requests.
2. Exposure is idempotent, so reloads do not inflate the denominator.
3. Events inherit the server-assigned variant; clients cannot choose an arm.
4. Results count distinct converted users, ignore pre-exposure events, and
   compute a correct two-proportion z-test.
5. The briefing exposes quick actions derived from deterministic scores.
"""

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from app.models.assignment import Assignment, AssignmentStatus
from app.models.experiment import (
    Experiment,
    ExperimentEvent,
    ExperimentExposure,
    ExperimentStatus,
)
from app.models.user import User
from app.routers import ai as ai_router
from app.services.experiments import (
    assign_variant,
    compute_results,
    two_proportion_z_test,
)
from app.services.scoring import ScoredSignal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _variants():
    return [
        {"key": "control", "weight": 50},
        {"key": "treatment", "weight": 50},
    ]


def _make_experiment(db, key="test_experiment", status=ExperimentStatus.running):
    experiment = Experiment(
        id=uuid.uuid4(),
        key=key,
        name="Test experiment",
        description="Test fixture",
        status=status,
        variants=_variants(),
        primary_metric="converted",
        started_at=datetime.now(timezone.utc),
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def _make_user(db, index):
    user = User(
        id=uuid.uuid4(),
        email=f"ab_user_{index}@lifeos.app",
        # These users are never authenticated, so skip bcrypt: hashing 200
        # passwords would dominate the test suite's runtime.
        hashed_password="not-a-real-hash",
        name=f"AB User {index}",
        monthly_budget=300,
        weekly_capacity_hours=40,
    )
    db.add(user)
    db.commit()
    return user


def _expose(db, experiment, user, variant, exposed_at=None):
    exposure = ExperimentExposure(
        id=uuid.uuid4(),
        experiment_id=experiment.id,
        user_id=user.id,
        variant=variant,
        first_exposed_at=exposed_at or datetime.now(timezone.utc),
    )
    db.add(exposure)
    db.commit()
    return exposure


def _event(db, experiment, user, variant, name="converted", occurred_at=None):
    event = ExperimentEvent(
        id=uuid.uuid4(),
        experiment_id=experiment.id,
        user_id=user.id,
        variant=variant,
        event_name=name,
        occurred_at=occurred_at or datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    return event


# ---------------------------------------------------------------------------
# Deterministic assignment
# ---------------------------------------------------------------------------


def test_assign_variant_is_deterministic():
    user_id = uuid.uuid4()
    variants = _variants()

    first = assign_variant("briefing_quick_complete", user_id, variants)
    for _ in range(50):
        assert assign_variant("briefing_quick_complete", user_id, variants) == first


def test_assign_variant_is_balanced_across_users():
    variants = _variants()
    counts = {"control": 0, "treatment": 0}

    # UUID(int=i) is reproducible, so this test cannot flake.
    for i in range(1000):
        variant = assign_variant("balance_test", uuid.UUID(int=i), variants)
        counts[variant] += 1

    assert counts["control"] + counts["treatment"] == 1000
    # SHA-256 behaves like a uniform hash; allow a generous margin.
    assert 400 <= counts["control"] <= 600


def test_assign_variant_is_independent_per_experiment():
    """The experiment key is part of the hash, so arms are not correlated."""
    user_id = uuid.uuid4()

    first = assign_variant("experiment_a", user_id, _variants())
    second = assign_variant("experiment_b", user_id, _variants())

    # For one fixed user the two can coincidentally match. Across many users,
    # at least one must differ or the key is not actually part of the hash.
    assignments = {
        (
            assign_variant("experiment_a", uuid.UUID(int=i), _variants()),
            assign_variant("experiment_b", uuid.UUID(int=i), _variants()),
        )
        for i in range(100)
    }
    assert len(assignments) > 2


def test_assign_variant_respects_zero_weight():
    variants = [
        {"key": "control", "weight": 100},
        {"key": "treatment", "weight": 0},
    ]

    for i in range(100):
        assert assign_variant("zero_weight", uuid.UUID(int=i), variants) == "control"


def test_assign_variant_normalizes_weights():
    variants = [
        {"key": "a", "weight": 33},
        {"key": "b", "weight": 33},
        {"key": "c", "weight": 34},
    ]

    seen = {
        assign_variant("three_arm", uuid.UUID(int=i), variants) for i in range(300)
    }
    assert seen == {"a", "b", "c"}


def test_assign_variant_rejects_empty_variants():
    with pytest.raises(ValueError):
        assign_variant("bad", uuid.uuid4(), [])


# ---------------------------------------------------------------------------
# Exposure
# ---------------------------------------------------------------------------


def test_exposure_is_idempotent(client, db_session, demo_user, auth_headers):
    experiment = _make_experiment(db_session)

    first = client.get(f"/experiments/{experiment.key}", **auth_headers)
    second = client.get(f"/experiments/{experiment.key}", **auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["variant"] == second.json()["variant"]
    assert first.json()["active"] is True

    exposures = db_session.query(ExperimentExposure).filter(
        ExperimentExposure.experiment_id == experiment.id
    ).all()
    assert len(exposures) == 1
    assert exposures[0].variant == first.json()["variant"]


def test_inactive_experiment_does_not_expose(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(
        db_session, status=ExperimentStatus.paused
    )

    response = client.get(f"/experiments/{experiment.key}", **auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["active"] is False
    assert data["variant"] is None
    assert db_session.query(ExperimentExposure).count() == 0


def test_unknown_experiment_returns_404(client, demo_user, auth_headers):
    response = client.get("/experiments/does_not_exist", **auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def test_event_inherits_server_assigned_variant(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(db_session)
    assignment = client.get(
        f"/experiments/{experiment.key}", **auth_headers
    ).json()

    response = client.post(
        f"/experiments/{experiment.key}/events",
        json={
            "event_name": "converted",
            "metadata": {"assignment_id": "abc"},
        },
        **auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["variant"] == assignment["variant"]
    assert data["counts_toward_primary"] is True

    event = db_session.query(ExperimentEvent).one()
    assert event.variant == assignment["variant"]
    assert event.event_metadata == {"assignment_id": "abc"}


def test_event_creates_exposure_when_missing(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(db_session)

    response = client.post(
        f"/experiments/{experiment.key}/events",
        json={"event_name": "converted"},
        **auth_headers,
    )

    assert response.status_code == 201
    exposure = db_session.query(ExperimentExposure).one()
    event = db_session.query(ExperimentEvent).one()
    assert event.variant == exposure.variant


def test_event_rejected_when_experiment_not_running(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(
        db_session, status=ExperimentStatus.completed
    )

    response = client.post(
        f"/experiments/{experiment.key}/events",
        json={"event_name": "converted"},
        **auth_headers,
    )

    assert response.status_code == 409
    assert db_session.query(ExperimentEvent).count() == 0


def test_non_primary_event_is_stored_but_not_counted(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(db_session)

    response = client.post(
        f"/experiments/{experiment.key}/events",
        json={"event_name": "some_other_metric"},
        **auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["counts_toward_primary"] is False


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


def test_two_proportion_z_test_known_values():
    result = two_proportion_z_test(10, 100, 20, 100)

    assert result["absolute_lift"] == pytest.approx(0.10)
    assert result["lift"] == pytest.approx(1.0)
    assert result["z_score"] == pytest.approx(1.9803, abs=1e-3)
    assert result["p_value"] == pytest.approx(0.0477, abs=1e-3)
    assert result["is_significant"] is True
    low, high = result["confidence_interval"]
    assert low < 0.10 < high


def test_two_proportion_z_test_handles_empty_arm():
    result = two_proportion_z_test(0, 0, 5, 10)

    assert result["p_value"] is None
    assert result["is_significant"] is False


def test_results_count_unique_users_and_ignore_other_events(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(db_session)
    control = _make_user(db_session, 1)
    treatment = _make_user(db_session, 2)

    _expose(db_session, experiment, control, "control")
    _expose(db_session, experiment, treatment, "treatment")

    # Treatment user converts twice: still one converted user.
    _event(db_session, experiment, treatment, "treatment")
    _event(db_session, experiment, treatment, "treatment")
    # A different metric must not count toward the primary metric.
    _event(db_session, experiment, treatment, "treatment", name="other")

    response = client.get(
        f"/experiments/{experiment.key}/results", **auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    by_variant = {v["variant"]: v for v in data["variants"]}
    assert by_variant["control"]["exposures"] == 1
    assert by_variant["control"]["conversions"] == 0
    assert by_variant["treatment"]["exposures"] == 1
    assert by_variant["treatment"]["conversions"] == 1
    assert data["total_exposures"] == 2


def test_results_ignore_events_before_exposure(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(db_session)
    user = _make_user(db_session, 3)
    exposed_at = datetime.now(timezone.utc)

    _expose(db_session, experiment, user, "treatment", exposed_at=exposed_at)
    _event(
        db_session,
        experiment,
        user,
        "treatment",
        occurred_at=exposed_at - timedelta(hours=1),
    )

    response = client.get(
        f"/experiments/{experiment.key}/results", **auth_headers
    )

    by_variant = {v["variant"]: v for v in response.json()["variants"]}
    assert by_variant["treatment"]["conversions"] == 0


def test_results_compute_lift_and_significance(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(db_session)
    now = datetime.now(timezone.utc)

    # 100 users per arm, 10% vs 20% conversion.
    for i in range(100):
        user = _make_user(db_session, 100 + i)
        _expose(db_session, experiment, user, "control", exposed_at=now)
        if i < 10:
            _event(db_session, experiment, user, "control", occurred_at=now)

    for i in range(100):
        user = _make_user(db_session, 200 + i)
        _expose(db_session, experiment, user, "treatment", exposed_at=now)
        if i < 20:
            _event(db_session, experiment, user, "treatment", occurred_at=now)

    response = client.get(
        f"/experiments/{experiment.key}/results", **auth_headers
    )

    data = response.json()
    by_variant = {v["variant"]: v for v in data["variants"]}
    control = by_variant["control"]
    treatment = by_variant["treatment"]

    assert control["conversion_rate"] == pytest.approx(0.10)
    assert treatment["conversion_rate"] == pytest.approx(0.20)
    assert treatment["lift"] == pytest.approx(1.0)
    assert treatment["is_significant"] is True
    assert data["sample_size_ok"] is True
    assert data["winning_variant"] == "treatment"


def test_results_are_preliminary_below_sample_threshold(
    client, db_session, demo_user, auth_headers
):
    experiment = _make_experiment(db_session)
    control = _make_user(db_session, 400)
    treatment = _make_user(db_session, 401)

    _expose(db_session, experiment, control, "control")
    _expose(db_session, experiment, treatment, "treatment")
    _event(db_session, experiment, treatment, "treatment")

    response = client.get(
        f"/experiments/{experiment.key}/results", **auth_headers
    )

    data = response.json()
    assert data["sample_size_ok"] is False
    assert any("Preliminary" in note for note in data["notes"])


def test_compute_results_returns_zeroed_payload_without_exposures(
    db_session,
):
    experiment = _make_experiment(db_session)

    results = compute_results(db_session, experiment)

    assert results["total_exposures"] == 0
    assert len(results["variants"]) == 2
    assert all(v["conversions"] == 0 for v in results["variants"])
    assert results["notes"]


def test_seed_experiments_is_idempotent(db_session):
    from app.seed import seed_experiments

    seed_experiments(db_session)
    seed_experiments(db_session)

    experiments = db_session.query(Experiment).filter(
        Experiment.key == "briefing_quick_complete"
    ).all()
    assert len(experiments) == 1
    assert experiments[0].status == ExperimentStatus.running
    assert experiments[0].primary_metric == "quick_action_completed"
    assert experiments[0].variants == [
        {"key": "control", "weight": 50},
        {"key": "treatment", "weight": 50},
    ]


# ---------------------------------------------------------------------------
# Briefing quick actions
# ---------------------------------------------------------------------------


def test_briefing_exposes_quick_actions(
    client, db_session, demo_user, auth_headers, monkeypatch
):
    monkeypatch.setattr(ai_router, "client", None)

    assignment = Assignment(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        title="DSA Assignment",
        course="CS201",
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        estimated_hours=5,
        status=AssignmentStatus.pending,
    )
    db_session.add(assignment)
    db_session.commit()

    response = client.post("/ai/briefing", **auth_headers)

    assert response.status_code == 200
    data = response.json()
    action = next(
        a for a in data["quick_actions"]
        if a["assignment_id"] == str(assignment.id)
    )
    assert action["title"] == "Due soon: DSA Assignment"
    assert action["course"] == "CS201"
    assert action["label"] == "Mark done"


def test_build_quick_actions_skips_non_assignment_signals():
    signals = [
        ScoredSignal(
            domain="job",
            title="Follow up: SWE Intern at Acme",
            reason="No response.",
            score=60,
            meta={"job_id": "job-1"},
        ),
        ScoredSignal(
            domain="assignment",
            title="Overdue: Essay",
            reason="Late.",
            score=55,
            meta={"assignment_id": "a-1", "course": "ENG101"},
        ),
        ScoredSignal(
            domain="assignment",
            title="Overdue: Essay duplicate",
            reason="Late.",
            score=50,
            meta={"assignment_id": "a-1", "course": "ENG101"},
        ),
    ]

    actions = ai_router.build_quick_actions(signals)

    assert len(actions) == 1
    assert actions[0]["assignment_id"] == "a-1"
