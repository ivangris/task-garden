from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import get_settings


WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


class SingleUserWriteAuthMiddleware(BaseHTTPMiddleware):
    """Small private-deployment gate; local development remains unauthenticated."""

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        if request.method not in WRITE_METHODS or not settings.write_auth_required:
            return await call_next(request)

        expected_token = (settings.single_user_auth_token or "").strip()
        if not expected_token:
            return JSONResponse(
                status_code=503,
                content={"detail": "Hosted write access is not configured. Set TASK_GARDEN_SINGLE_USER_AUTH_TOKEN."},
            )

        provided_token = _extract_bearer_token(request.headers.get("Authorization"))
        if provided_token != expected_token:
            return JSONResponse(status_code=401, content={"detail": "A valid Task Garden access token is required."})

        return await call_next(request)
