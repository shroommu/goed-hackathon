from __future__ import annotations

import json
import logging
import os
from functools import wraps
from typing import Any, Callable, TypeVar

import jwt
import requests
from flask import Response, g, jsonify, request
from sqlalchemy import text

from .extensions import db

F = TypeVar("F", bound=Callable[..., Any])

SUPABASE_AUTH_TIMEOUT_SECONDS = int(os.getenv("SUPABASE_AUTH_TIMEOUT_SECONDS", "10"))

audit_logger = logging.getLogger("app.auth_audit")


def error_envelope(
    status: int, code: str, message: str, details: dict | None = None
) -> tuple[Response, int]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status


def _normalize_role_string(raw: object) -> str | None:
    if isinstance(raw, str):
        s = raw.strip().lower()
        return s if s else None
    return None


def _app_metadata_admin(app_metadata: object) -> bool:
    if not isinstance(app_metadata, dict):
        return False
    role = _normalize_role_string(app_metadata.get("role"))
    return role == "admin"


def _user_dict_from_claims(
    *, sub: str, email: object, app_metadata: object
) -> dict[str, Any]:
    meta = app_metadata if isinstance(app_metadata, dict) else {}
    return {
        "id": sub,
        "email": email if isinstance(email, str) else None,
        "app_metadata": meta,
        "is_admin": _app_metadata_admin(meta),
    }


def _supabase_auth_api_key() -> str | None:
    return (
        os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
    )


def _verify_via_supabase_user_endpoint(
    token: str,
) -> tuple[dict[str, Any] | None, tuple[Response, int] | None]:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = _supabase_auth_api_key()

    if not supabase_url or not supabase_key:
        audit_logger.info(
            json.dumps(
                {
                    "event": "token_verify_failure",
                    "reason": "auth_not_configured",
                }
            )
        )
        return None, error_envelope(
            503,
            "auth_unavailable",
            "Supabase auth verification is not configured.",
            {
                "required": [
                    "SUPABASE_URL",
                    "SUPABASE_PUBLISHABLE_KEY or SUPABASE_ANON_KEY",
                ]
            },
        )

    endpoint = f"{supabase_url.rstrip('/')}/auth/v1/user"
    try:
        response = requests.get(
            endpoint,
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=SUPABASE_AUTH_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        audit_logger.info(
            json.dumps(
                {
                    "event": "token_verify_failure",
                    "reason": "auth_endpoint_unreachable",
                    "detail": str(exc),
                }
            )
        )
        return None, error_envelope(
            503,
            "auth_unavailable",
            "Unable to reach Supabase auth verification endpoint.",
            {"reason": str(exc)},
        )

    if response.status_code in {401, 403}:
        audit_logger.info(
            json.dumps(
                {
                    "event": "token_verify_failure",
                    "reason": "invalid_or_expired_token",
                    "status_code": response.status_code,
                }
            )
        )
        return None, error_envelope(
            401, "invalid_auth_token", "Invalid or expired auth token."
        )

    if response.status_code >= 400:
        audit_logger.info(
            json.dumps(
                {
                    "event": "token_verify_failure",
                    "reason": "auth_provider_error",
                    "status_code": response.status_code,
                }
            )
        )
        return None, error_envelope(
            502,
            "auth_provider_error",
            "Supabase auth provider returned an error.",
            {"status_code": response.status_code, "response": response.text},
        )

    user = response.json()
    user_id = user.get("id")
    if not user_id:
        audit_logger.info(
            json.dumps({"event": "token_verify_failure", "reason": "missing_user_id"})
        )
        return None, error_envelope(
            401, "invalid_auth_token", "Auth token did not include user id."
        )

    app_metadata = user.get("app_metadata")
    return (
        _user_dict_from_claims(
            sub=str(user_id),
            email=user.get("email"),
            app_metadata=app_metadata,
        ),
        None,
    )


def verify_supabase_token(
    token: str,
) -> tuple[dict[str, Any] | None, tuple[Response, int] | None]:
    """Verify JWT (local HS256 when configured) or fall back to Supabase /user."""
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if secret:
        try:
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"require": ["exp", "sub"]},
            )
        except jwt.ExpiredSignatureError:
            audit_logger.info(
                json.dumps({"event": "token_verify_failure", "reason": "expired"})
            )
            return None, error_envelope(
                401, "invalid_auth_token", "Invalid or expired auth token."
            )
        except jwt.InvalidTokenError as exc:
            audit_logger.info(
                json.dumps(
                    {
                        "event": "token_verify_failure",
                        "reason": "invalid_token",
                        "detail": str(exc),
                    }
                )
            )
            return None, error_envelope(
                401, "invalid_auth_token", "Invalid or expired auth token."
            )

        sub = claims.get("sub")
        if not sub:
            audit_logger.info(
                json.dumps({"event": "token_verify_failure", "reason": "missing_sub"})
            )
            return None, error_envelope(
                401, "invalid_auth_token", "Auth token did not include subject."
            )

        return (
            _user_dict_from_claims(
                sub=str(sub),
                email=claims.get("email"),
                app_metadata=claims.get("app_metadata"),
            ),
            None,
        )

    return _verify_via_supabase_user_endpoint(token)


def get_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header[7:].strip()
    return token or None


def get_current_user() -> tuple[dict[str, Any] | None, tuple[Response, int] | None]:
    token = get_bearer_token()
    if not token:
        return None, error_envelope(
            401,
            "missing_auth_token",
            "Authorization header with Bearer token is required.",
        )
    return verify_supabase_token(token)


def log_auth_401(*, endpoint: str, action: str) -> None:
    audit_logger.info(
        json.dumps({"event": "auth_401", "endpoint": endpoint, "action": action})
    )


def log_auth_403(*, endpoint: str, action: str, user_id: str | None) -> None:
    audit_logger.info(
        json.dumps(
            {
                "event": "auth_403",
                "endpoint": endpoint,
                "action": action,
                "user_id": user_id,
            }
        )
    )


def log_admin_mutation_success(
    *, actor_user_id: str, target: dict[str, Any]
) -> None:
    audit_logger.info(
        json.dumps(
            {
                "event": "admin_mutation_success",
                "actor_user_id": actor_user_id,
                "target": target,
            }
        )
    )


def log_owner_edit_success(*, actor_user_id: str, company_id: int) -> None:
    audit_logger.info(
        json.dumps(
            {
                "event": "owner_edit_success",
                "actor_user_id": actor_user_id,
                "company_id": company_id,
            }
        )
    )


def _table_columns(table_name: str) -> set[str]:
    inspector = db.inspect(db.engine)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_exists(table_name: str) -> bool:
    inspector = db.inspect(db.engine)
    return table_name in inspector.get_table_names()


def _claim_status_column(columns: set[str]) -> str | None:
    if "status" in columns:
        return "status"
    if "STATUS" in columns:
        return '"STATUS"'
    return None


def is_verified_company_owner(user_id: str, company_id: int) -> bool:
    if not _table_exists("claim_requests"):
        return False
    columns = _table_columns("claim_requests")
    status_column = _claim_status_column(columns)
    if not status_column or "user_id" not in columns:
        return False

    row = db.session.execute(
        text(f"""
            SELECT 1
            FROM claim_requests
            WHERE company_id = :company_id
              AND user_id = :user_id
              AND LOWER({status_column}) = 'verified'
            LIMIT 1
            """),
        {"company_id": company_id, "user_id": user_id},
    ).first()
    return row is not None


def owner_or_admin_for_company(
    user: dict[str, Any], company_id: int
) -> tuple[Response, int] | None:
    """Return None if allowed; otherwise a 403 error envelope."""
    if user.get("is_admin"):
        return None
    if is_verified_company_owner(str(user["id"]), company_id):
        return None
    log_auth_403(
        endpoint=request.path,
        action="update_company_protected",
        user_id=str(user.get("id")),
    )
    return error_envelope(
        403,
        "ownership_required",
        "Only verified owners or admins can edit protected fields.",
        {"company_id": company_id, "user_id": user.get("id")},
    )


def require_auth(*, action: str = "request") -> Callable[[F], F]:
    def decorator(f: F) -> F:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any):
            user, err = get_current_user()
            if err:
                log_auth_401(endpoint=request.path, action=action)
                return err
            g.auth_user = user
            return f(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    return decorator


def require_admin(*, action: str = "admin") -> Callable[[F], F]:
    def decorator(f: F) -> F:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any):
            user, err = get_current_user()
            if err:
                log_auth_401(endpoint=request.path, action=action)
                return err
            if not user.get("is_admin"):
                log_auth_403(
                    endpoint=request.path,
                    action=action,
                    user_id=str(user.get("id")),
                )
                return error_envelope(
                    403,
                    "admin_required",
                    "This action requires admin privileges.",
                    {"user_id": user.get("id")},
                )
            g.auth_user = user
            return f(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    return decorator
