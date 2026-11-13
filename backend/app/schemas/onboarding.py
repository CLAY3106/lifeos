"""
Onboarding Schemas: Wizard Event Validation

This module defines the Pydantic model for the onboarding event endpoint:
1. OnboardingEventIn: A single wizard progress event

The event name is constrained with Literal so unknown actions are rejected
at request parsing time (422) instead of reaching the activity log.
"""

from typing import Literal, Optional

from pydantic import BaseModel

# The five wizard events the frontend is allowed to record.
OnboardingEventName = Literal[
    "onboarding_started",
    "onboarding_step_completed",
    "onboarding_skipped",
    "onboarding_completed",
    "first_briefing_viewed",
]


class OnboardingEventIn(BaseModel):
    """
    Request body for POST /onboarding/events.

    - event: One of the five onboarding actions
    - step: Wizard step number (1-4). Required when the event is
      onboarding_step_completed; validated in the router so failures
      return 400 rather than a schema-level 422.
    """
    event: OnboardingEventName
    step: Optional[int] = None
