"""
Experiment Models — A/B Testing Storage

Three tables support the experiment framework:

1. experiments
   The configuration: a unique key, the variant weights, and the primary
   metric. Variants are stored as JSON rather than a separate table because
   they are a small, ordered configuration list that is read as a whole.

2. experiment_exposures
   One row per (experiment, user): the first time the user was shown a
   variant. The unique constraint is what makes exposure idempotent — page
   reloads and React re-renders cannot inflate the denominator.

3. experiment_events
   Every conversion event. Events are intentionally not unique: a user may
   complete several assignments. Results count distinct converted users, so
   repeated events do not inflate the numerator.

Why store the variant on both exposures and events?
----------------------------------------------------
The exposure is the source of truth for a user's assignment. Copying the
variant onto the event makes results queries a direct join and preserves what
the user actually saw even if the experiment configuration changes later.
"""

import enum
import uuid

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.base import TimestampMixin


class ExperimentStatus(enum.Enum):
    """Lifecycle of an experiment.

    Only `running` experiments assign variants and accept events. Paused and
    completed experiments keep their historical rows for analysis.
    """

    draft = "draft"
    running = "running"
    paused = "paused"
    completed = "completed"


class Experiment(Base, TimestampMixin):
    """An A/B test definition.

    `variants` is an ordered list of {"key": str, "weight": float} objects.
    The first variant is treated as the control in results. Weights are
    percentages and should sum to 100.
    """

    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(ExperimentStatus), nullable=False, default=ExperimentStatus.draft
    )
    variants = Column(JSON, nullable=False, default=list)
    primary_metric = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)


class ExperimentExposure(Base, TimestampMixin):
    """A user's first exposure to an experiment variant.

    The unique constraint on (experiment_id, user_id) is the idempotency
    guarantee. The variant is never changed after creation, so a user who was
    exposed before a weight change keeps their original assignment.
    """

    __tablename__ = "experiment_exposures"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id", "user_id", name="uq_experiment_exposure_user"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant = Column(String, nullable=False)
    first_exposed_at = Column(DateTime, nullable=False)


class ExperimentEvent(Base, TimestampMixin):
    """An immutable conversion event.

    `event_metadata` is a JSON payload for context such as the assignment that
    was completed. It is named `event_metadata` because `metadata` is reserved
    by SQLAlchemy's declarative system.
    """

    __tablename__ = "experiment_events"
    __table_args__ = (
        Index(
            "ix_experiment_events_experiment_metric",
            "experiment_id",
            "event_name",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    occurred_at = Column(DateTime, nullable=False)
