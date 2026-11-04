"""
Experiment Service — Deterministic Bucketing, Exposure, and Statistics

The three responsibilities that make an A/B test trustworthy:

1. Assignment is deterministic.
   SHA-256(experiment_key + user_id) maps a user to a bucket. There is no
   random number to persist and no chance of a user flipping variants between
   requests. Including the experiment key in the hash gives each experiment an
   independent assignment, so a user is not always in the same arm across
   unrelated tests.

2. Exposure and conversion are separate.
   An exposure is "this user actually saw the variant." A conversion is "this
   user did the thing." Conversion rate is conversions / exposures, never
   conversions / all users. The unique constraint on exposures makes the
   denominator idempotent across reloads.

3. Results use a two-proportion z-test.
   The pooled standard error tests whether the difference in conversion rates
   is larger than sampling noise. The p-value is two-sided because either arm
   could win. The confidence interval uses the unpooled standard error, which
   is the right choice for estimating the size of the difference.

This is intentionally dependency-free: no scipy, no stats library. `math.erf`
and `math.erfc` are enough for a normal approximation.
"""

import hashlib
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.experiment import (
    Experiment,
    ExperimentEvent,
    ExperimentExposure,
)
from app.models.user import User

# Bucket resolution. 10,000 buckets gives 0.01% precision, which is far more
# than enough for a 50/50 split and keeps weight math easy to reason about.
BUCKET_COUNT = 10_000

# Two-sided 95% normal critical value.
Z_95 = 1.959963984540054

# Below this many exposures per arm, a conversion-rate difference is too noisy
# to act on. Results still compute, but the response flags the sample size.
MIN_EXPOSURES_PER_VARIANT = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _variant_keys(variants: list[dict]) -> list[str]:
    """Return variant keys in configuration order (control first)."""
    return [variant["key"] for variant in variants]


def assign_variant(experiment_key: str, user_id, variants: list[dict]) -> str:
    """
    Deterministically assign a user to a variant.

    The hash input is `experiment_key:user_id`. The experiment key is part of
    the hash so two experiments do not produce correlated assignments: the
    same user can be in control for one test and treatment for another.

    Weights are normalized rather than assumed to sum to 100. That makes the
    function forgiving of a configuration such as 33/33/34 while keeping the
    split exact. A zero-weight variant is never assigned.

    Raises:
        ValueError: if there are no variants or all weights are non-positive.
    """
    if not variants:
        raise ValueError("Experiment has no variants")

    weights = [max(float(v.get("weight", 0)), 0.0) for v in variants]
    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError("Experiment variants have no positive weight")

    # SHA-256, not Python's hash(): built-in hashing is randomized per process,
    # so assignments would change on every deploy.
    digest = hashlib.sha256(
        f"{experiment_key}:{user_id}".encode("utf-8")
    ).hexdigest()
    bucket = int(digest[:8], 16) % BUCKET_COUNT

    threshold = 0.0
    for variant, weight in zip(variants, weights):
        if weight == 0:
            continue
        threshold += (weight / total_weight) * BUCKET_COUNT
        if bucket < threshold:
            return variant["key"]

    # Floating-point drift can leave the final bucket just above the last
    # threshold. Fall back to the last positive-weight variant.
    for variant, weight in zip(reversed(variants), reversed(weights)):
        if weight > 0:
            return variant["key"]
    raise ValueError("Experiment variants have no positive weight")


def get_exposure(
    db: Session, experiment: Experiment, user: User
) -> Optional[ExperimentExposure]:
    """Return the user's existing exposure, if any."""
    return (
        db.query(ExperimentExposure)
        .filter(
            ExperimentExposure.experiment_id == experiment.id,
            ExperimentExposure.user_id == user.id,
        )
        .first()
    )


def get_or_create_exposure(
    db: Session,
    experiment: Experiment,
    user: User,
    variant: Optional[str] = None,
) -> ExperimentExposure:
    """
    Return the user's exposure, creating it on first sight.

    The unique constraint on (experiment_id, user_id) is the idempotency
    guarantee. Two concurrent first requests can both miss the SELECT; the
    loser of the INSERT race catches IntegrityError, rolls back, and reads the
    row the winner committed.

    If the user already has an exposure, its variant is returned unchanged —
    even if `variant` was passed or the experiment weights changed. Switching
    a user mid-experiment would contaminate both arms.
    """
    existing = get_exposure(db, experiment, user)
    if existing:
        return existing

    assigned = variant or assign_variant(
        experiment.key, user.id, experiment.variants
    )
    exposure = ExperimentExposure(
        id=uuid.uuid4(),
        experiment_id=experiment.id,
        user_id=user.id,
        variant=assigned,
        first_exposed_at=_now(),
    )
    db.add(exposure)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return (
            db.query(ExperimentExposure)
            .filter(
                ExperimentExposure.experiment_id == experiment.id,
                ExperimentExposure.user_id == user.id,
            )
            .one()
        )

    db.refresh(exposure)
    return exposure


def record_event(
    db: Session,
    experiment: Experiment,
    exposure: ExperimentExposure,
    event_name: str,
    value: Optional[float] = None,
    event_metadata: Optional[dict] = None,
) -> ExperimentEvent:
    """
    Persist an immutable conversion event.

    Events are not deduplicated: a user can complete multiple assignments.
    Results count distinct users, so extra events do not inflate the metric.
    """
    event = ExperimentEvent(
        id=uuid.uuid4(),
        experiment_id=experiment.id,
        user_id=exposure.user_id,
        variant=exposure.variant,
        event_name=event_name,
        value=value,
        event_metadata=event_metadata,
        occurred_at=_now(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def two_proportion_z_test(
    control_conversions: int,
    control_exposures: int,
    treatment_conversions: int,
    treatment_exposures: int,
) -> dict:
    """
    Compare two conversion rates with a two-sided two-proportion z-test.

    Pooled standard error is used for the test statistic (the null hypothesis
    is that both arms share one true rate). Unpooled standard error is used for
    the confidence interval (we are estimating a difference, not testing a
    null).

    Returns None values rather than raising when an arm has no exposures, so a
    brand-new experiment can still return a useful results payload.
    """
    if control_exposures == 0 or treatment_exposures == 0:
        return {
            "absolute_lift": None,
            "lift": None,
            "z_score": None,
            "p_value": None,
            "confidence_interval": None,
            "is_significant": False,
        }

    p_control = control_conversions / control_exposures
    p_treatment = treatment_conversions / treatment_exposures
    difference = p_treatment - p_control

    pooled = (control_conversions + treatment_conversions) / (
        control_exposures + treatment_exposures
    )
    pooled_se = math.sqrt(
        pooled
        * (1 - pooled)
        * (1 / control_exposures + 1 / treatment_exposures)
    )

    if pooled_se == 0:
        # Both arms are 0% or both are 100%: there is no variance to test.
        z_score = 0.0
        p_value = 1.0
    else:
        z_score = difference / pooled_se
        # Two-sided p = 2 * (1 - Phi(|z|)) = erfc(|z| / sqrt(2)).
        # erfc avoids catastrophic cancellation in the tail.
        p_value = math.erfc(abs(z_score) / math.sqrt(2))

    unpooled_se = math.sqrt(
        p_control * (1 - p_control) / control_exposures
        + p_treatment * (1 - p_treatment) / treatment_exposures
    )
    margin = Z_95 * unpooled_se

    return {
        "absolute_lift": round(difference, 6),
        "lift": (
            round(difference / p_control, 6) if p_control > 0 else None
        ),
        "z_score": round(z_score, 6),
        "p_value": round(p_value, 6),
        "confidence_interval": [
            round(difference - margin, 6),
            round(difference + margin, 6),
        ],
        "is_significant": p_value < 0.05,
    }


def compute_results(db: Session, experiment: Experiment) -> dict:
    """
    Aggregate exposures and unique conversions per variant.

    Only events at or after the user's first exposure are counted. That
    prevents a pre-existing action from being attributed to a variant the user
    had not seen yet.

    The numerator counts distinct users, not events: completing three
    assignments is still one converted user.
    """
    exposure_rows = (
        db.query(ExperimentExposure.variant, func.count(ExperimentExposure.id))
        .filter(ExperimentExposure.experiment_id == experiment.id)
        .group_by(ExperimentExposure.variant)
        .all()
    )
    exposures_by_variant = {variant: count for variant, count in exposure_rows}

    conversion_rows = (
        db.query(
            ExperimentExposure.variant,
            func.count(func.distinct(ExperimentEvent.user_id)),
        )
        .join(
            ExperimentEvent,
            and_(
                ExperimentEvent.experiment_id
                == ExperimentExposure.experiment_id,
                ExperimentEvent.user_id == ExperimentExposure.user_id,
                ExperimentEvent.variant == ExperimentExposure.variant,
                ExperimentEvent.event_name == experiment.primary_metric,
                ExperimentEvent.occurred_at
                >= ExperimentExposure.first_exposed_at,
            ),
        )
        .filter(ExperimentExposure.experiment_id == experiment.id)
        .group_by(ExperimentExposure.variant)
        .all()
    )
    conversions_by_variant = {variant: count for variant, count in conversion_rows}

    results = []
    for variant_key in _variant_keys(experiment.variants):
        exposures = exposures_by_variant.get(variant_key, 0)
        conversions = conversions_by_variant.get(variant_key, 0)
        results.append(
            {
                "variant": variant_key,
                "exposures": exposures,
                "conversions": conversions,
                "conversion_rate": (
                    round(conversions / exposures, 6) if exposures else 0.0
                ),
                # Control gets no comparison statistics.
                "absolute_lift": None,
                "lift": None,
                "z_score": None,
                "p_value": None,
                "confidence_interval": None,
                "is_significant": False,
            }
        )

    # The first configured variant is the control. Every other variant is
    # compared against it.
    if len(results) > 1:
        control = results[0]
        for treatment in results[1:]:
            treatment.update(
                two_proportion_z_test(
                    control["conversions"],
                    control["exposures"],
                    treatment["conversions"],
                    treatment["exposures"],
                )
            )

    total_exposures = sum(r["exposures"] for r in results)
    sample_size_ok = bool(results) and all(
        r["exposures"] >= MIN_EXPOSURES_PER_VARIANT for r in results
    )

    significant = [r for r in results if r["is_significant"]]
    winning_variant = None
    if significant:
        winner = max(significant, key=lambda r: r["conversion_rate"])
        winning_variant = winner["variant"]

    notes = []
    if total_exposures == 0:
        notes.append("No exposures yet. Visit the experiment surface to enroll users.")
    elif not sample_size_ok:
        notes.append(
            f"Preliminary: at least {MIN_EXPOSURES_PER_VARIANT} exposures per "
            "variant are recommended before acting on the result."
        )

    return {
        "key": experiment.key,
        "name": experiment.name,
        "status": experiment.status.value,
        "primary_metric": experiment.primary_metric,
        "total_exposures": total_exposures,
        "sample_size_ok": sample_size_ok,
        "winning_variant": winning_variant,
        "variants": results,
        "notes": notes,
    }
