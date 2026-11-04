"""
Experiments Router — Variant Assignment, Events, and Results

Endpoints:
1. GET  /experiments/{key}          — evaluate the current user and record exposure
2. POST /experiments/{key}/events   — log a conversion event
3. GET  /experiments/{key}/results  — aggregate conversion rates and significance

The GET endpoint has an intentional side effect: it records the user's first
exposure. Exposure is "the user was shown the experiment surface," and the
evaluation call is the moment that happens. Making exposure a separate request
would let the client forget to send it and silently shrink the denominator.
The write is idempotent, so reloads are safe.

Events are resolved server-side from the exposure table. The client sends only
the event name and metadata; it cannot choose its variant.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.experiment import Experiment, ExperimentStatus
from app.models.user import User
from app.schemas.experiment import (
    ExperimentAssignmentResponse,
    ExperimentEventCreate,
    ExperimentEventResponse,
    ExperimentResultsResponse,
)
from app.services.experiments import (
    compute_results,
    get_or_create_exposure,
    record_event,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _get_experiment(db: Session, key: str) -> Experiment:
    """Load an experiment by its stable public key, or 404."""
    experiment = db.query(Experiment).filter(Experiment.key == key).first()
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )
    return experiment


def _require_running(experiment: Experiment) -> None:
    """Reject assignment/events for experiments that are not accepting data."""
    if experiment.status != ExperimentStatus.running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Experiment is {experiment.status.value}, not running",
        )


@router.get("/{key}", response_model=ExperimentAssignmentResponse)
def get_assignment(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluate the current user's variant and record the exposure.

    If the experiment is not running, return an inactive assignment with a null
    variant. Clients should render the control experience in that case.
    """
    experiment = _get_experiment(db, key)

    if experiment.status != ExperimentStatus.running:
        return ExperimentAssignmentResponse(
            key=experiment.key,
            name=experiment.name,
            status=experiment.status.value,
            active=False,
            variant=None,
            primary_metric=experiment.primary_metric,
        )

    exposure = get_or_create_exposure(db, experiment, current_user)
    return ExperimentAssignmentResponse(
        key=experiment.key,
        name=experiment.name,
        status=experiment.status.value,
        active=True,
        variant=exposure.variant,
        primary_metric=experiment.primary_metric,
    )


@router.post(
    "/{key}/events",
    response_model=ExperimentEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    key: str,
    data: ExperimentEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a conversion event for the current user.

    The variant comes from the user's exposure, never from the request body.
    If the user has no exposure yet (for example, a race where the event fires
    before the assignment call), the exposure is created first so the event is
    still attributable.
    """
    experiment = _get_experiment(db, key)
    _require_running(experiment)

    exposure = get_or_create_exposure(db, experiment, current_user)
    event = record_event(
        db=db,
        experiment=experiment,
        exposure=exposure,
        event_name=data.event_name,
        value=data.value,
        event_metadata=data.metadata,
    )

    return ExperimentEventResponse(
        event_id=str(event.id),
        variant=event.variant,
        counts_toward_primary=data.event_name == experiment.primary_metric,
    )


@router.get("/{key}/results", response_model=ExperimentResultsResponse)
def get_results(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregate results for an experiment.

    Results are readable by any authenticated user for now. The admin/ops
    layer will move this behind an admin role once that exists; keeping it
    authenticated today avoids blocking the demo and still prevents anonymous
    access to product metrics.
    """
    experiment = _get_experiment(db, key)
    return compute_results(db, experiment)
