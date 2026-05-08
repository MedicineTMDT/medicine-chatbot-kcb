import base64
import json
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _decode_json_part(value: str) -> dict[str, Any]:
    try:
        return json.loads(_base64url_decode(value))
    except (ValueError, json.JSONDecodeError):
        raise _unauthorized("Invalid JWT")


async def _get_request_user_id(request: Request) -> str | None:
    query_user_id = request.query_params.get("user_id")
    if query_user_id:
        return query_user_id

    if request.method not in {"POST", "PUT", "PATCH"}:
        return None

    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        return None

    try:
        body = await request.json()
    except ValueError:
        return None

    if not isinstance(body, dict):
        return None

    user_id = body.get("user_id")
    return str(user_id) if user_id is not None else None


def decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise _unauthorized("Invalid JWT")

    _, encoded_payload, _ = parts
    payload = _decode_json_part(encoded_payload)

    return payload


async def require_jwt_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None:
        raise _unauthorized("Missing bearer token")

    if credentials.scheme.lower() != "bearer":
        raise _unauthorized("Invalid authorization scheme")

    payload = decode_jwt_payload(credentials.credentials)
    token_user_id = payload.get("sub")
    request_user_id = await _get_request_user_id(request)

    if request_user_id is not None and request_user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id does not match token subject",
        )

    return payload
