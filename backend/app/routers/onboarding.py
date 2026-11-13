"""
Onboarding Router: Wizard Progress Events

Records onboarding progress in the existing activity log instead of a
dedicated table. One endpoint, five events:

- onboarding_started
- onboarding_step_completed (step 1-4)
- onboarding_skipped
- onboarding_completed
- first_briefing_viewed

When onboarding_completed arrives, the server also stamps
user.onboarding_completed_at (if not already set) so completion is
recorded even if the client never PATCHes /auth/me. Both paths are
idempotent: repeated events only add activity rows, and the timestamp
is written at most once.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.activity_log import ActivityLogResponse
from app.schemas.onboarding import OnboardingEventIn
from app.services.activity_log_service import log_activity

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/events", response_model=ActivityLogResponse)
def create_onboarding_event(
    data: OnboardingEventIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record an onboarding wizard event for the current user.

    Writes an activity log entry (entity_type "onboarding") and returns it,
    matching the shape of GET /activity. For onboarding_completed it also
    sets onboarding_completed_at once, making server-side completion
    idempotent with the PATCH /auth/me path.
    """
    if data.event == "onboarding_step_completed" and data.step is None:
        raise HTTPException(
            status_code=400,
            detail="step is required for onboarding_step_completed",
        )
    if data.step is not None and not 1 <= data.step <= 4:
        raise HTTPException(status_code=400, detail="step must be between 1 and 4")

    if data.event == "onboarding_completed" and current_user.onboarding_completed_at is None:
        current_user.onboarding_completed_at = datetime.now(timezone.utc)

    # log_activity commits, which also persists the timestamp set above.
    return log_activity(
        db,
        current_user.id,
        action=data.event,
        entity_type="onboarding",
        details=f"step={data.step}" if data.step is not None else None,
    )
