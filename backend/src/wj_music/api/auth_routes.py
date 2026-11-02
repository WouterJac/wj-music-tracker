"""Token check for the API and the pairing route. Routes only call the service."""

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from wj_music.services.auth import AuthDecision, AuthService, RateLimitedError

# Pairing is how a client gets the token, so it cannot need one.
OPEN_API_PATHS = frozenset({"/api/pair"})


class PairRequest(BaseModel):
    code: str = Field(max_length=64)


class PairResponse(BaseModel):
    token: str


def _client(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def install_token_check(app: FastAPI, service: AuthService) -> None:
    """Every /api request needs the Bearer token. /health and the frontend stay open."""

    @app.middleware("http")
    async def require_token(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if path.startswith("/api/") and path not in OPEN_API_PATHS:
            decision = service.check_request(request.headers.get("authorization"), _client(request))
            if decision is AuthDecision.UNAUTHORIZED:
                return JSONResponse(
                    {"detail": "Authentication required"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if decision is AuthDecision.RATE_LIMITED:
                return JSONResponse({"detail": "Too many failed attempts"}, status_code=429)
        return await call_next(request)


def auth_router(service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.post("/pair")
    def pair(body: PairRequest, request: Request) -> PairResponse:
        try:
            token = service.pair(body.code, _client(request))
        except RateLimitedError:
            raise HTTPException(
                status_code=429, detail="Too many failed attempts. Try again in a minute."
            ) from None
        if token is None:
            raise HTTPException(status_code=401, detail="That code is wrong or has expired")
        return PairResponse(token=token)

    return router
