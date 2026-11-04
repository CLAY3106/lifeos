"""
Embedding Service — OpenAI Vectors with a Circuit Breaker

Turns text into vectors for semantic search. The rest of the app must keep
working when OpenAI is unavailable (no key, no credits, network down), so this
module never raises on API failure — it returns an empty result instead.

Circuit breaker
---------------
A failed embedding call is usually not isolated: if the account is out of
credits or the key is invalid, every subsequent call fails the same way. Left
alone, each briefing/search request would pay that latency (up to two 10s
timeouts) before degrading.

After a failure the breaker opens for a cooldown window. While open, callers
get an empty result immediately. This is what keeps keyword-only RAG fast
instead of merely correct. Cooldowns are longer for permanent failures
(insufficient quota, bad key) than for transient ones (network, burst limits).
"""

import os
import threading
import time

import openai

# Load .env before reading OPENAI_API_KEY
import app.config  # noqa: F401
from app.logger import logger

_client = None

# --- Circuit breaker state -------------------------------------------------
# time.monotonic() is immune to wall-clock changes (NTP, DST), which matters
# for measuring elapsed time. A lock is required because FastAPI runs sync
# endpoints in a threadpool.
_CIRCUIT_COOLDOWN_SECONDS = 60
_CIRCUIT_PERMANENT_COOLDOWN_SECONDS = 900

_circuit_open_until = 0.0
_circuit_reason = ""
_circuit_lock = threading.Lock()


def _get_client() -> openai.OpenAI:
    """
    Create the OpenAI client on first use instead of at import time.

    Creating it lazily means the app still starts (and every non-RAG feature
    keeps working) when OPENAI_API_KEY is missing. The error surfaces only
    when an embedding is actually requested.
    """
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        _client = openai.OpenAI(
            api_key=api_key,
            timeout=10.0,     # fail fast instead of hanging a request
            max_retries=1,    # one retry for transient 429s, then degrade
        )
    return _client


def _circuit_is_open() -> bool:
    with _circuit_lock:
        return time.monotonic() < _circuit_open_until


def _trip_circuit(reason: str, cooldown: int = _CIRCUIT_COOLDOWN_SECONDS) -> None:
    """Open the breaker for `cooldown` seconds and record why."""
    global _circuit_open_until, _circuit_reason
    with _circuit_lock:
        _circuit_open_until = time.monotonic() + cooldown
        _circuit_reason = reason
    logger.warning(
        "embedding_circuit_open",
        reason=reason,
        cooldown_seconds=cooldown,
    )


def _reset_circuit() -> None:
    """Close the breaker after a successful call."""
    global _circuit_open_until, _circuit_reason
    with _circuit_lock:
        _circuit_open_until = 0.0
        _circuit_reason = ""


def _handle_failure(exc: Exception) -> None:
    """
    Translate an OpenAI exception into a circuit-breaker cooldown.

    `insufficient_quota` and authentication failures will not fix themselves,
    so they get a long cooldown. Everything else is treated as transient.
    """
    if isinstance(exc, openai.AuthenticationError):
        _trip_circuit("authentication_error", _CIRCUIT_PERMANENT_COOLDOWN_SECONDS)
        return

    if isinstance(exc, openai.RateLimitError):
        body = getattr(exc, "body", None)
        # OpenAI has used both fields over time: `type: insufficient_quota`
        # with `code: credit_balance_exhausted`, and older `code:
        # insufficient_quota`. Check both so billing failures get the long
        # cooldown instead of being retried every minute.
        signal = None
        if isinstance(body, dict):
            signal = body.get("code") or body.get("type")
        if signal in {
            "insufficient_quota",
            "credit_balance_exhausted",
            "billing_hard_limit_reached",
        }:
            _trip_circuit(str(signal), _CIRCUIT_PERMANENT_COOLDOWN_SECONDS)
        else:
            _trip_circuit(f"rate_limit:{signal or 'unknown'}")
        return

    _trip_circuit(type(exc).__name__)


def get_embedding(text: str) -> list[float]:
    """Convert text to a vector. Returns [] when embeddings are unavailable."""
    if _circuit_is_open():
        logger.debug("embedding_skipped", reason="circuit_open")
        return []

    try:
        response = _get_client().embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        _reset_circuit()
        return response.data[0].embedding
    except Exception as exc:  # noqa: BLE001 — degradation is the contract
        logger.warning(
            "embedding_failed",
            error_type=type(exc).__name__,
            error=str(exc)[:200],
        )
        _handle_failure(exc)
        return []


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Convert a list of texts to vectors. Returns [] per item on failure."""
    if not texts:
        return []

    if _circuit_is_open():
        logger.debug("embedding_batch_skipped", reason="circuit_open", count=len(texts))
        return [[] for _ in texts]

    try:
        response = _get_client().embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        _reset_circuit()
        # The API may return items out of order; sort by index before mapping.
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
    except Exception as exc:  # noqa: BLE001 — degradation is the contract
        logger.warning(
            "embedding_batch_failed",
            error_type=type(exc).__name__,
            error=str(exc)[:200],
            count=len(texts),
        )
        _handle_failure(exc)
        return [[] for _ in texts]
