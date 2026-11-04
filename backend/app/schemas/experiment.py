"""
Experiment Schemas — API Contracts for A/B Testing

1. ExperimentAssignmentResponse: the current user's variant for an experiment
2. ExperimentEventCreate: a conversion event from the client
3. ExperimentEventResponse: confirmation that an event was stored
4. ExperimentResultsResponse: aggregate conversion rates and significance

The client never sends its variant. The server resolves it from the exposure
table (or the deterministic bucket) so a modified request cannot claim to be
in the other arm.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ExperimentAssignmentResponse(BaseModel):
    """The evaluated assignment for the current user.

    `active` is false when the experiment is not running. In that case
    `variant` is null and clients should render the control experience.
    """

    key: str
    name: str
    status: str
    active: bool
    variant: Optional[str] = None
    primary_metric: str


class ExperimentEventCreate(BaseModel):
    """A conversion event submitted by an authenticated client."""

    event_name: str = Field(..., min_length=1, max_length=100)
    value: Optional[float] = None
    metadata: Optional[dict] = None


class ExperimentEventResponse(BaseModel):
    """Confirmation of a stored event.

    `counts_toward_primary` is false when the event name is not the
    experiment's primary metric. The event is still stored for future
    secondary analysis, but it will not move the headline result.
    """

    status: str = "ok"
    event_id: str
    variant: str
    counts_toward_primary: bool = True


class VariantResult(BaseModel):
    """One variant's exposure, conversion, and comparison statistics.

    Comparison fields are null for the control and for any arm with no
    exposures. `lift` is relative to control; `absolute_lift` is the
    percentage-point difference.
    """

    variant: str
    exposures: int
    conversions: int
    conversion_rate: float
    absolute_lift: Optional[float] = None
    lift: Optional[float] = None
    z_score: Optional[float] = None
    p_value: Optional[float] = None
    confidence_interval: Optional[List[float]] = None
    is_significant: bool = False


class ExperimentResultsResponse(BaseModel):
    """Aggregate results for one experiment."""

    key: str
    name: str
    status: str
    primary_metric: str
    total_exposures: int
    sample_size_ok: bool
    winning_variant: Optional[str] = None
    variants: List[VariantResult]
    notes: List[str] = Field(default_factory=list)
