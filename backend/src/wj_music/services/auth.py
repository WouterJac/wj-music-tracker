"""Remote access use cases: check the access token, and hand it out for a one-time pairing code."""

import hmac
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum

from wj_music.domain.auth import FailureLimiter, new_pairing_code, normalise_code
from wj_music.domain.repositories import PairingCodes

PAIRING_TTL = timedelta(minutes=5)


class AuthDecision(Enum):
    ALLOWED = "allowed"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"


class RateLimitedError(Exception):
    """Too many failed attempts from one client."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, _, rest = authorization.partition(" ")
    token = rest.strip()
    return token if scheme.lower() == "bearer" and token else None


class AuthService:
    def __init__(
        self,
        token: str,
        pairing: PairingCodes,
        limiter: FailureLimiter,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._token = token
        self._pairing = pairing
        self._limiter = limiter
        self._clock = clock

    def check_request(self, authorization: str | None, client: str) -> AuthDecision:
        presented = _bearer_token(authorization)
        if presented is None:
            # Not counted as a failure: an app that has not paired yet asks for many things at once.
            return AuthDecision.UNAUTHORIZED
        now = self._clock()
        if self._limiter.is_blocked(client, now):
            return AuthDecision.RATE_LIMITED
        if hmac.compare_digest(presented.encode(), self._token.encode()):
            return AuthDecision.ALLOWED
        self._limiter.record_failure(client, now)
        return AuthDecision.UNAUTHORIZED

    def pair(self, code: str, client: str) -> str | None:
        """The access token if the code is valid and unused, else None."""
        now = self._clock()
        if self._limiter.is_blocked(client, now):
            raise RateLimitedError
        if self._pairing.redeem(normalise_code(code), now):
            return self._token
        self._limiter.record_failure(client, now)
        return None

    def issue_pairing_code(self) -> tuple[str, datetime]:
        code = new_pairing_code()
        expires_at = self._clock() + PAIRING_TTL
        self._pairing.issue(code, expires_at)
        return code, expires_at
