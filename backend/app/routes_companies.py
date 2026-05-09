from __future__ import annotations

import json
import os
import re
from urllib.parse import urlparse

import requests
from flask import Flask, g, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, NoSuchTableError, OperationalError

from .auth import (
    log_admin_mutation_success,
    log_owner_edit_success,
    owner_or_admin_for_company,
    require_admin,
    require_auth,
)
from .extensions import db

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_COMPANY_PER_PAGE = 100
SUPABASE_REST_TIMEOUT_SECONDS = int(os.getenv("SUPABASE_REST_TIMEOUT_SECONDS", "10"))
SUPABASE_AUTH_TIMEOUT_SECONDS = int(os.getenv("SUPABASE_AUTH_TIMEOUT_SECONDS", "10"))

ALLOWED_STAGE_FILTERS = {
    "idea",
    "pre-seed",
    "seed",
    "series-a",
    "series-b",
    "series-c",
    "growth",
    "late-stage",
    "public",
    "unknown",
}

SIZE_BUCKETS = {
    "micro": (1, 10),
    "small": (11, 50),
    "medium": (51, 200),
    "large": (201, 500),
    "enterprise": (501, None),
}

PROTECTED_COMPANY_FIELDS = {
    "description",
    "website",
    "stage",
    "employees",
    "sector",
    "full_address",
    "linkedin",
}

CLAIM_STATUS_PENDING = "pending"
CLAIM_STATUS_VERIFIED = "verified"
CLAIM_STATUS_REJECTED = "rejected"
CLAIM_STATUS_VALUES = {
    CLAIM_STATUS_PENDING,
    CLAIM_STATUS_VERIFIED,
    CLAIM_STATUS_REJECTED,
}
CLAIM_DECISION_TO_STATUS = {
    "approve": CLAIM_STATUS_VERIFIED,
    "reject": CLAIM_STATUS_REJECTED,
}


def _error_response(status: int, code: str, message: str, details: dict | None = None):
    payload = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status


def _request_json_object():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error_response(
            400,
            "invalid_request_body",
            "Request body must be a JSON object.",
        )
    return payload, None


def _non_empty_string_field(payload: dict, field_name: str):
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        return None, _error_response(
            400,
            "invalid_request_body",
            f"'{field_name}' is required and must be a non-empty string.",
            {"field": field_name},
        )
    return value.strip(), None


def _parse_positive_int(raw: str | None, *, field_name: str, default: int):
    if raw is None:
        return default, None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, _error_response(
            400,
            "invalid_query_parameter",
            f"'{field_name}' must be an integer.",
            {"field": field_name, "value": raw},
        )

    if value < 1:
        return None, _error_response(
            400,
            "invalid_query_parameter",
            f"'{field_name}' must be greater than or equal to 1.",
            {"field": field_name, "value": raw},
        )

    return value, None


def _table_columns(table_name: str) -> set[str]:
    inspector = db.inspect(db.engine)
    try:
        return {column["name"] for column in inspector.get_columns(table_name)}
    except NoSuchTableError:
        return set()


def _table_exists(table_name: str) -> bool:
    inspector = db.inspect(db.engine)
    return table_name in inspector.get_table_names()


def _first_present_column(columns: set[str], *candidates: str) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _extract_domain(raw_website: str | None) -> str | None:
    if not raw_website:
        return None

    candidate = raw_website.strip()
    if not candidate:
        return None

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _claim_status_from_row(row: dict) -> str | None:
    raw_status = row.get("status")
    if raw_status is None:
        raw_status = row.get("STATUS")
    if raw_status is None:
        return None
    status_text = str(raw_status).strip().lower()
    return status_text or None


def _claim_requested_updates(row: dict) -> dict:
    raw = row.get("requested_updates")
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        text_value = raw.strip()
        if not text_value:
            return {}
        try:
            decoded = json.loads(text_value)
        except json.JSONDecodeError:
            return {}
        if isinstance(decoded, dict):
            return decoded
    return {}


def _serialize_claim_row(row: dict) -> dict:
    requested_updates = _claim_requested_updates(row)
    payload = {
        "id": row.get("id"),
        "company_id": row.get("company_id"),
        "user_id": row.get("user_id"),
        "status": _claim_status_from_row(row),
        "role_at_company": requested_updates.get("role_at_company"),
        "claimant_note": row.get("message"),
    }

    if row.get("submitter_email"):
        payload["submitter_email"] = row.get("submitter_email")

    return payload


def _claim_verification_history(claim_id: int) -> list[dict]:
    if not _table_exists("verification_events"):
        return []

    verification_columns = _table_columns("verification_events")
    if "claim_request_id" not in verification_columns:
        return []

    select_parts = ["id", "event_type", "actor_email", "notes"]
    if "created_at" in verification_columns:
        select_parts.append("created_at")
    else:
        select_parts.append("NULL AS created_at")

    rows = db.session.execute(
        text(f"""
            SELECT {', '.join(select_parts)}
            FROM verification_events
            WHERE claim_request_id = :claim_id
            ORDER BY id ASC
            """),
        {"claim_id": claim_id},
    ).mappings()

    events: list[dict] = []
    for row in rows:
        event_payload = {
            "id": row.get("id"),
            "event_type": row.get("event_type"),
            "actor_email": row.get("actor_email"),
            "notes": row.get("notes"),
        }
        if row.get("created_at") is not None:
            event_payload["created_at"] = str(row.get("created_at"))
        events.append(event_payload)

    return events


def _append_verification_event(
    *,
    claim_id: int,
    event_type: str,
    actor_email: str | None,
    notes: str | None,
) -> None:
    if not _table_exists("verification_events"):
        return

    verification_columns = _table_columns("verification_events")
    event_values: dict[str, object] = {}
    if "claim_request_id" in verification_columns:
        event_values["claim_request_id"] = claim_id
    if "event_type" in verification_columns:
        event_values["event_type"] = event_type
    if "actor_email" in verification_columns and actor_email:
        event_values["actor_email"] = actor_email
    if "notes" in verification_columns and notes:
        event_values["notes"] = notes

    if not event_values:
        return

    event_columns = sorted(event_values.keys())
    event_params = {f"v_{column}": event_values[column] for column in event_columns}
    event_column_csv = ", ".join(event_columns)
    event_values_csv = ", ".join(f":v_{column}" for column in event_columns)

    db.session.execute(
        text(f"""
            INSERT INTO verification_events ({event_column_csv})
            VALUES ({event_values_csv})
            """),
        event_params,
    )


def _serialize_company_for_response(row: dict) -> dict:
    return _normalize_company_row(dict(row), photo_gallery=[])


def _find_domain_duplicates(*, company_id: int, website: str | None) -> list[int]:
    website_domain = _extract_domain(website)
    if not website_domain:
        return []

    columns = _table_columns("companies")
    website_column = _first_present_column(columns, "website")
    if not website_column:
        return []

    rows = db.session.execute(
        text(f"""
            SELECT id, {website_column} AS website
            FROM companies
            WHERE id <> :company_id AND {website_column} IS NOT NULL
            """),
        {"company_id": company_id},
    ).mappings()

    duplicates: list[int] = []
    for row in rows:
        row_domain = _extract_domain(row.get("website"))
        if row_domain and row_domain == website_domain:
            duplicates.append(int(row.get("id")))

    return sorted(duplicates)


def _create_company_listing(payload: dict):
    startup_name, error = _non_empty_string_field(payload, "startup_name")
    if error:
        return error

    website, error = _non_empty_string_field(payload, "website")
    if error:
        return error

    columns = _table_columns("companies")
    if not columns:
        return _error_response(
            503,
            "data_source_unavailable",
            "Companies table is unavailable.",
        )

    name_column = _first_present_column(columns, "startup_name", "name")
    website_column = _first_present_column(columns, "website")

    if not name_column or not website_column:
        return _error_response(
            500,
            "schema_mismatch",
            "Companies schema is missing required listing columns.",
        )

    values: dict[str, object] = {
        name_column: startup_name,
        website_column: website,
    }

    column_mapping = {
        "description": ["description"],
        "stage": ["stage"],
        "sector": ["sector"],
        "full_address": ["full_address", "address"],
        "linkedin": ["linkedin", "linkedin_url"],
        "display_type": ["display_type"],
    }

    for field_name, candidates in column_mapping.items():
        if field_name not in payload:
            continue
        target_column = _first_present_column(columns, *candidates)
        if not target_column:
            continue
        raw_value = payload.get(field_name)
        if raw_value is None:
            continue
        text_value = str(raw_value).strip()
        if text_value:
            values[target_column] = text_value

    employees_target = _first_present_column(columns, "employees", "employee_count")
    if employees_target and payload.get("employees") is not None:
        if employees_target == "employee_count":
            coerced = _coerce_int(payload.get("employees"))
            if coerced is not None:
                values[employees_target] = coerced
        else:
            employees_text = str(payload.get("employees")).strip()
            if employees_text:
                values[employees_target] = employees_text

    insert_columns = sorted(values.keys())
    params = {f"v_{name}": values[name] for name in insert_columns}
    column_csv = ", ".join(insert_columns)
    values_csv = ", ".join(f":v_{name}" for name in insert_columns)

    company_id = db.session.execute(
        text(f"""
            INSERT INTO companies ({column_csv})
            VALUES ({values_csv})
            RETURNING id
            """),
        params,
    ).scalar_one()
    db.session.commit()

    row = (
        db.session.execute(
            text("SELECT * FROM companies WHERE id = :id AND archived = FALSE"),
            {"id": company_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        return _error_response(
            500,
            "listing_creation_failed",
            "Listing was created but could not be loaded.",
        )

    return (
        jsonify(
            {
                "item": _serialize_company_for_response(dict(row)),
                "duplicate_domain_matches": _find_domain_duplicates(
                    company_id=company_id,
                    website=website,
                ),
            }
        ),
        201,
    )


def _claim_status_column(columns: set[str]) -> str | None:
    if "status" in columns:
        return "status"
    if "STATUS" in columns:
        return '"STATUS"'
    return None


def _claims_pending_or_verified_exists(company_id: int, status_column: str):
    return (
        db.session.execute(
            text(f"""
                SELECT id, LOWER({status_column}) AS status
                FROM claim_requests
                WHERE company_id = :company_id
                  AND LOWER({status_column}) IN ('pending', 'verified')
                LIMIT 1
                """),
            {"company_id": company_id},
        )
        .mappings()
        .first()
    )


def _has_pending_claim_for_user(*, user_id: str, status_column: str):
    columns = _table_columns("claim_requests")
    if "user_id" not in columns:
        return None

    return (
        db.session.execute(
            text(f"""
                SELECT id, company_id
                FROM claim_requests
                WHERE user_id = :user_id
                  AND LOWER({status_column}) = 'pending'
                LIMIT 1
                """),
            {"user_id": user_id},
        )
        .mappings()
        .first()
    )


def _company_exists(company_id: int) -> bool:
    row = db.session.execute(
        text(
            "SELECT 1 FROM companies WHERE id = :company_id AND archived = FALSE LIMIT 1"
        ),
        {"company_id": company_id},
    ).first()
    return row is not None


def _create_claim_request(*, company_id: int, payload: dict, user: dict):
    role_at_company, error = _non_empty_string_field(payload, "role_at_company")
    if error:
        return error

    claimant_note = payload.get("claimant_note")
    if claimant_note is not None and not isinstance(claimant_note, str):
        return _error_response(
            400,
            "invalid_request_body",
            "'claimant_note' must be a string when provided.",
            {"field": "claimant_note"},
        )

    if not _company_exists(company_id):
        return _error_response(
            404,
            "company_not_found",
            "Company not found.",
            {"company_id": company_id},
        )

    columns = _table_columns("claim_requests")
    status_column = _claim_status_column(columns)
    if not status_column:
        return _error_response(
            500,
            "schema_mismatch",
            "Claim requests schema is missing status column.",
        )

    existing_active_claim = _claims_pending_or_verified_exists(
        company_id, status_column
    )
    if existing_active_claim:
        return _error_response(
            409,
            "claim_conflict",
            "Company already has an active ownership claim.",
            {
                "company_id": company_id,
                "existing_claim_id": existing_active_claim.get("id"),
                "existing_status": existing_active_claim.get("status"),
            },
        )

    existing_user_pending = _has_pending_claim_for_user(
        user_id=user["id"],
        status_column=status_column,
    )
    if existing_user_pending:
        return _error_response(
            409,
            "claim_conflict",
            "User already has an active pending claim.",
            {
                "user_id": user["id"],
                "existing_claim_id": existing_user_pending.get("id"),
                "existing_company_id": existing_user_pending.get("company_id"),
            },
        )

    insert_values: dict[str, object] = {"company_id": company_id}

    if "submitter_email" in columns and user.get("email"):
        insert_values["submitter_email"] = user["email"]
    if "submitter_name" in columns and user.get("email"):
        insert_values["submitter_name"] = str(user["email"]).split("@", 1)[0]
    if "status" in columns:
        insert_values["status"] = "pending"
    elif "STATUS" in columns:
        insert_values["STATUS"] = "pending"
    if "message" in columns and claimant_note:
        insert_values["message"] = claimant_note.strip()
    if "requested_updates" in columns:
        insert_values["requested_updates"] = json.dumps(
            {
                "role_at_company": role_at_company,
            }
        )
    if "user_id" in columns:
        insert_values["user_id"] = user["id"]

    insert_columns = sorted(insert_values.keys())
    params = {f"v_{column}": insert_values[column] for column in insert_columns}
    column_csv = ", ".join(insert_columns)
    values_csv = ", ".join(f":v_{column}" for column in insert_columns)

    claim_id = db.session.execute(
        text(f"""
            INSERT INTO claim_requests ({column_csv})
            VALUES ({values_csv})
            RETURNING id
            """),
        params,
    ).scalar_one()

    _append_verification_event(
        claim_id=claim_id,
        event_type="claim_submitted",
        actor_email=user.get("email"),
        notes=f"role_at_company={role_at_company}",
    )

    db.session.commit()
    return (
        jsonify(
            {
                "item": {
                    "id": claim_id,
                    "company_id": company_id,
                    "user_id": user["id"],
                    "status": "pending",
                    "role_at_company": role_at_company,
                    "claimant_note": (
                        claimant_note.strip()
                        if isinstance(claimant_note, str)
                        else None
                    ),
                }
            }
        ),
        201,
    )


def _user_claim_for_company(*, company_id: int, user: dict):
    if not _company_exists(company_id):
        return _error_response(
            404,
            "company_not_found",
            "Company not found.",
            {"company_id": company_id},
        )

    columns = _table_columns("claim_requests")
    status_column = _claim_status_column(columns)
    if not status_column or "user_id" not in columns:
        return _error_response(
            500,
            "schema_mismatch",
            "Claim requests schema is missing required columns.",
        )

    row = (
        db.session.execute(
            text("""
                SELECT *
                FROM claim_requests
                WHERE company_id = :company_id
                  AND user_id = :user_id
                ORDER BY id DESC
                LIMIT 1
                                """),
            {
                "company_id": company_id,
                "user_id": user["id"],
            },
        )
        .mappings()
        .first()
    )

    if row is None:
        return _error_response(
            404,
            "claim_not_found",
            "Claim not found for this user and company.",
            {
                "company_id": company_id,
                "user_id": user["id"],
            },
        )

    item = _serialize_claim_row(dict(row))
    item["verification_events"] = _claim_verification_history(int(item["id"]))
    return jsonify({"item": item}), 200


def _list_claim_requests(*, status: str | None):
    columns = _table_columns("claim_requests")
    status_column = _claim_status_column(columns)
    if not status_column:
        return _error_response(
            500,
            "schema_mismatch",
            "Claim requests schema is missing status column.",
        )

    where_clauses: list[str] = []
    params: dict[str, object] = {}
    if status:
        where_clauses.append(f"LOWER({status_column}) = :status")
        params["status"] = status

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    rows = db.session.execute(
        text(f"""
            SELECT *
            FROM claim_requests
            {where_sql}
            ORDER BY id DESC
            LIMIT 200
            """),
        params,
    ).mappings()

    items: list[dict] = []
    for row in rows:
        item = _serialize_claim_row(dict(row))
        item["verification_events"] = _claim_verification_history(int(item["id"]))
        items.append(item)

    return jsonify({"items": items, "filters": {"status": status}}), 200


def _admin_decide_claim(*, claim_id: int, payload: dict, admin_user: dict):
    decision, error = _non_empty_string_field(payload, "decision")
    if error:
        return error
    decision = decision.lower()
    if decision not in CLAIM_DECISION_TO_STATUS:
        return _error_response(
            400,
            "invalid_request_body",
            "'decision' has an invalid value.",
            {
                "field": "decision",
                "value": decision,
                "allowed_values": sorted(CLAIM_DECISION_TO_STATUS.keys()),
            },
        )

    raw_notes = payload.get("notes")
    if raw_notes is not None and not isinstance(raw_notes, str):
        return _error_response(
            400,
            "invalid_request_body",
            "'notes' must be a string when provided.",
            {"field": "notes"},
        )
    notes = raw_notes.strip() if isinstance(raw_notes, str) else None

    columns = _table_columns("claim_requests")
    status_column = _claim_status_column(columns)
    if not status_column:
        return _error_response(
            500,
            "schema_mismatch",
            "Claim requests schema is missing status column.",
        )

    row = (
        db.session.execute(
            text("""
                SELECT *
                FROM claim_requests
                WHERE id = :claim_id
                LIMIT 1
                """),
            {"claim_id": claim_id},
        )
        .mappings()
        .first()
    )

    if row is None:
        return _error_response(
            404,
            "claim_not_found",
            "Claim request not found.",
            {"claim_id": claim_id},
        )

    current_status = _claim_status_from_row(dict(row))
    if current_status != CLAIM_STATUS_PENDING:
        return _error_response(
            409,
            "verification_conflict",
            "Only pending claims can be approved or rejected.",
            {
                "claim_id": claim_id,
                "status": current_status,
            },
        )

    new_status = CLAIM_DECISION_TO_STATUS[decision]
    assignments = [f"{status_column} = :new_status"]
    if "updated_at" in columns:
        assignments.append("updated_at = CURRENT_TIMESTAMP")

    try:
        db.session.execute(
            text(f"""
                UPDATE claim_requests
                SET {', '.join(assignments)}
                WHERE id = :claim_id
                """),
            {
                "claim_id": claim_id,
                "new_status": new_status,
            },
        )

        event_type = "claim_approved" if decision == "approve" else "claim_rejected"
        _append_verification_event(
            claim_id=claim_id,
            event_type=event_type,
            actor_email=admin_user.get("email"),
            notes=notes,
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error_response(
            409,
            "claim_conflict",
            "Claim decision conflicts with an existing active ownership claim.",
            {"claim_id": claim_id, "decision": decision},
        )

    log_admin_mutation_success(
        actor_user_id=str(admin_user["id"]),
        target={
            "type": "claim_request",
            "claim_id": claim_id,
            "decision": decision,
        },
    )

    updated_row = (
        db.session.execute(
            text("""
                SELECT *
                FROM claim_requests
                WHERE id = :claim_id
                LIMIT 1
                """),
            {"claim_id": claim_id},
        )
        .mappings()
        .first()
    )
    if updated_row is None:
        return _error_response(
            500,
            "verification_update_failed",
            "Claim decision was saved but the updated claim could not be loaded.",
            {"claim_id": claim_id},
        )

    item = _serialize_claim_row(dict(updated_row))
    item["verification_events"] = _claim_verification_history(int(item["id"]))
    return jsonify({"item": item}), 200


def _update_company_protected_fields(*, company_id: int, payload: dict, user: dict):
    if not payload:
        return _error_response(
            400,
            "invalid_request_body",
            "At least one protected field must be provided.",
        )

    unknown_fields = [
        field for field in payload if field not in PROTECTED_COMPANY_FIELDS
    ]
    if unknown_fields:
        return _error_response(
            400,
            "invalid_request_body",
            "Request includes unsupported fields.",
            {
                "fields": sorted(unknown_fields),
                "allowed_fields": sorted(PROTECTED_COMPANY_FIELDS),
            },
        )

    if not _company_exists(company_id):
        return _error_response(
            404,
            "company_not_found",
            "Company not found.",
            {"company_id": company_id},
        )

    denied = owner_or_admin_for_company(user, company_id)
    if denied:
        return denied

    columns = _table_columns("companies")
    field_to_column = {
        "description": _first_present_column(columns, "description"),
        "website": _first_present_column(columns, "website"),
        "stage": _first_present_column(columns, "stage"),
        "employees": _first_present_column(columns, "employees", "employee_count"),
        "sector": _first_present_column(columns, "sector"),
        "full_address": _first_present_column(columns, "full_address", "address"),
        "linkedin": _first_present_column(columns, "linkedin", "linkedin_url"),
    }

    assignments: list[str] = []
    params: dict[str, object] = {"company_id": company_id}
    for field_name, raw_value in payload.items():
        column_name = field_to_column.get(field_name)
        if not column_name:
            continue

        if field_name == "employees" and column_name == "employee_count":
            params[field_name] = _coerce_int(raw_value)
        elif raw_value is None:
            params[field_name] = None
        else:
            params[field_name] = str(raw_value).strip() or None

        assignments.append(f"{column_name} = :{field_name}")

    if not assignments:
        return _error_response(
            400,
            "invalid_request_body",
            "None of the provided fields can be updated with current schema.",
        )

    if "updated_at" in columns:
        assignments.append("updated_at = CURRENT_TIMESTAMP")

    db.session.execute(
        text(f"""
            UPDATE companies
            SET {', '.join(assignments)}
            WHERE id = :company_id
            """),
        params,
    )
    db.session.commit()

    if user.get("is_admin"):
        log_admin_mutation_success(
            actor_user_id=str(user["id"]),
            target={"type": "company", "company_id": company_id, "operation": "patch_protected"},
        )
    else:
        log_owner_edit_success(
            actor_user_id=str(user["id"]), company_id=company_id
        )

    try:
        return _get_company(company_id)
    except OperationalError:
        return _supabase_get_company(company_id)


def _supabase_request_headers() -> tuple[dict[str, str] | None, tuple | None]:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        return None, _error_response(
            503,
            "data_source_unavailable",
            "Supabase REST fallback is not configured.",
            {
                "required": ["SUPABASE_URL", "SUPABASE_SECRET_KEY"],
            },
        )

    return (
        {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Accept": "application/json",
            "Prefer": "count=exact",
        },
        None,
    )


def _supabase_count_from_content_range(
    content_range: str | None, returned_items: int
) -> int:
    if not content_range or "/" not in content_range:
        return returned_items
    total_part = content_range.split("/")[-1].strip()
    if total_part == "*":
        return returned_items
    try:
        return int(total_part)
    except ValueError:
        return returned_items


def _company_from_supabase_row(
    row: dict, *, photo_gallery: list[str] | None = None
) -> dict:
    mapped = {
        "id": row.get("id"),
        "display_type": row.get("display_type"),
        "linkedin": row.get("linkedin"),
        "startup_name": row.get("startup_name"),
        "full_address": row.get("full_address"),
        "description": row.get("description"),
        "website": row.get("website"),
        "stage": row.get("stage"),
        "employees": row.get("employees"),
        "sector": row.get("sector"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
    }
    return _normalize_company_row(mapped, photo_gallery=photo_gallery)


def _supabase_company_photo_gallery(company_id: int) -> list[str]:
    headers, error = _supabase_request_headers()
    if error:
        return []

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    endpoint = f"{supabase_url}/rest/v1/company_media"

    try:
        response = requests.get(
            endpoint,
            headers=headers,
            params={
                "select": "media_url",
                "company_id": f"eq.{company_id}",
                "order": "sort_order.asc,id.asc",
            },
            timeout=SUPABASE_REST_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return []

    if response.status_code >= 400:
        return []

    rows = response.json()
    return [
        str(row.get("media_url")).strip()
        for row in rows
        if row.get("media_url") and str(row.get("media_url")).strip()
    ]


def _supabase_list_companies(
    *,
    page: int,
    per_page: int,
    sector: str | None,
    size: str | None,
    stage: str | None,
    location: str | None,
):
    headers, error = _supabase_request_headers()
    if error:
        return error

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    endpoint = f"{supabase_url}/rest/v1/companies"

    params: dict[str, str | int] = {
        "select": (
            "id,display_type,linkedin,startup_name,full_address,description,"
            "website,stage,employees,sector,latitude,longitude"
        ),
        "order": "sector.asc.nullslast,stage.asc.nullslast,startup_name.asc.nullslast,id.asc",
        "limit": per_page,
        "offset": (page - 1) * per_page,
    }

    if sector:
        params["sector"] = f"ilike.*{sector.strip()}*"
    if stage:
        params["stage"] = f"eq.{stage}"
    if location:
        location_term = location.strip()
        params["full_address"] = f"ilike.*{location_term}*"

    try:
        response = requests.get(
            endpoint,
            headers=headers,
            params=params,
            timeout=SUPABASE_REST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return _error_response(
            503,
            "data_source_unavailable",
            "Failed to reach Supabase REST API.",
            {"source": "supabase_rest", "reason": str(exc)},
        )

    if response.status_code >= 400:
        return _error_response(
            502,
            "supabase_rest_error",
            "Supabase REST API returned an error.",
            {
                "source": "supabase_rest",
                "status_code": response.status_code,
                "response": response.text,
            },
        )

    rows = response.json()
    companies = [_company_from_supabase_row(row) for row in rows]

    if size:
        companies = [item for item in companies if item.get("size") == size]

    total = _supabase_count_from_content_range(
        response.headers.get("content-range"),
        len(companies),
    )

    if not companies:
        return _error_response(
            404,
            "companies_not_found",
            "No companies matched the provided filters.",
            {
                "filters": {
                    "sector": sector,
                    "size": size,
                    "stage": stage,
                    "location": location,
                }
            },
        )

    total_pages = (total + per_page - 1) // per_page if total else 0
    if total_pages and page > total_pages:
        return _error_response(
            400,
            "invalid_query_parameter",
            "'page' exceeds available pages for the current query.",
            {
                "field": "page",
                "value": page,
                "total_pages": total_pages,
            },
        )

    return (
        jsonify(
            {
                "items": companies,
                "mindmap": {
                    "levels": ["sector", "stage", "company"],
                    "sectors": _build_mindmap_hierarchy(companies),
                },
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": total_pages,
                },
                "filters": {
                    "sector": sector,
                    "size": size,
                    "stage": stage,
                    "location": location,
                },
            }
        ),
        200,
    )


def _supabase_get_company(company_id: int):
    headers, error = _supabase_request_headers()
    if error:
        return error

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    endpoint = f"{supabase_url}/rest/v1/companies"
    params = {
        "select": (
            "id,display_type,linkedin,startup_name,full_address,description,"
            "website,stage,employees,sector,latitude,longitude"
        ),
        "id": f"eq.{company_id}",
        "limit": 1,
    }

    try:
        response = requests.get(
            endpoint,
            headers=headers,
            params=params,
            timeout=SUPABASE_REST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return _error_response(
            503,
            "data_source_unavailable",
            "Failed to reach Supabase REST API.",
            {"source": "supabase_rest", "reason": str(exc)},
        )

    if response.status_code >= 400:
        return _error_response(
            502,
            "supabase_rest_error",
            "Supabase REST API returned an error.",
            {
                "source": "supabase_rest",
                "status_code": response.status_code,
                "response": response.text,
            },
        )

    rows = response.json()
    if not rows:
        return _error_response(
            404,
            "company_not_found",
            "Company not found.",
            {"company_id": company_id},
        )

    company = _company_from_supabase_row(
        rows[0],
        photo_gallery=_supabase_company_photo_gallery(company_id),
    )
    return jsonify({"item": company}), 200


def _normalize_company_string(value: object) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    text_value = str(value).strip()
    if not text_value:
        return None

    digits = re.sub(r"[^0-9]", "", text_value)
    if not digits:
        return None

    try:
        return int(digits)
    except ValueError:
        return None


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text_value = str(value).strip()
    if not text_value:
        return None
    try:
        return float(text_value)
    except ValueError:
        return None


def _compute_company_size_bucket(employee_count: int | None) -> str | None:
    if employee_count is None or employee_count < 1:
        return None
    for bucket, (min_size, max_size) in SIZE_BUCKETS.items():
        if max_size is None and employee_count >= min_size:
            return bucket
        if max_size is not None and min_size <= employee_count <= max_size:
            return bucket
    return None


def _parse_enum_filter(
    raw: str | None,
    *,
    field_name: str,
    allowed_values: set[str],
):
    if raw is None:
        return None, None

    value = raw.strip().lower()
    if not value:
        return None, None
    if value not in allowed_values:
        return None, _error_response(
            400,
            "invalid_query_parameter",
            f"'{field_name}' has an invalid value.",
            {
                "field": field_name,
                "value": raw,
                "allowed_values": sorted(allowed_values),
            },
        )
    return value, None


def _company_columns() -> set[str]:
    inspector = db.inspect(db.engine)
    return {column["name"] for column in inspector.get_columns("companies")}


def _company_media_available() -> bool:
    inspector = db.inspect(db.engine)
    return "company_media" in inspector.get_table_names()


def _parse_size_filter(raw: str | None):
    if raw is None:
        return None, None
    value = raw.strip().lower()
    if not value:
        return None, None
    if value not in SIZE_BUCKETS:
        return None, _error_response(
            400,
            "invalid_query_parameter",
            "'size' has an invalid value.",
            {
                "field": "size",
                "value": raw,
                "allowed_values": sorted(SIZE_BUCKETS.keys()),
            },
        )
    return value, None


def _build_company_select(columns: set[str]) -> str:
    select_parts = ["id"]
    optional_columns = [
        "display_type",
        "linkedin",
        "startup_name",
        "full_address",
        "description",
        "website",
        "stage",
        "employees",
        "sector",
        "latitude",
        "longitude",
    ]

    for column_name in optional_columns:
        if column_name in columns:
            select_parts.append(column_name)
        else:
            select_parts.append(f"NULL AS {column_name}")

    return ", ".join(select_parts)


def _company_employee_sql(columns: set[str]) -> str:
    if "employees" in columns:
        return "NULLIF(REGEXP_REPLACE(COALESCE(employees, ''), '[^0-9]', '', 'g'), '')::int"
    return "NULL::int"


def _company_name_sql(columns: set[str]) -> str:
    if "startup_name" in columns:
        return "startup_name"
    return "NULL"


def _company_location_sql(columns: set[str]) -> str:
    if "full_address" in columns:
        return "COALESCE(full_address, '')"
    return "''"


def _normalize_company_row(
    row: dict, *, photo_gallery: list[str] | None = None
) -> dict:
    employees = _normalize_company_string(row.get("employees"))
    employee_count = _coerce_int(employees)
    address = _normalize_company_string(row.get("full_address"))
    startup_name = _normalize_company_string(row.get("startup_name"))

    return {
        "id": row.get("id"),
        "display_type": _normalize_company_string(row.get("display_type")),
        "linkedin": _normalize_company_string(row.get("linkedin")),
        "startup_name": startup_name,
        "full_address": address,
        "description": _normalize_company_string(row.get("description")),
        "website": _normalize_company_string(row.get("website")),
        "stage": _normalize_company_string(row.get("stage")),
        "employees": employees,
        "sector": _normalize_company_string(row.get("sector")),
        "latitude": _coerce_float(row.get("latitude")),
        "longitude": _coerce_float(row.get("longitude")),
        "employee_count": employee_count,
        "size": _compute_company_size_bucket(employee_count),
        "photo_gallery": photo_gallery or [],
    }


def _build_mindmap_hierarchy(companies: list[dict]) -> list[dict]:
    hierarchy: dict[str, dict[str, list[dict]]] = {}

    for company in companies:
        sector = company.get("sector") or "Unknown"
        stage = company.get("stage") or "Unknown"
        hierarchy.setdefault(sector, {}).setdefault(stage, []).append(
            {"id": company.get("id"), "name": company.get("startup_name")}
        )

    sectors: list[dict] = []
    for sector in sorted(hierarchy.keys(), key=lambda value: value.lower()):
        stages = hierarchy[sector]
        stage_nodes = []
        for stage in sorted(stages.keys(), key=lambda value: value.lower()):
            companies_for_stage = sorted(
                stages[stage],
                key=lambda item: (
                    str(item.get("name") or "").lower(),
                    item.get("id") or 0,
                ),
            )
            stage_nodes.append({"name": stage, "companies": companies_for_stage})
        sectors.append({"name": sector, "stages": stage_nodes})

    return sectors


def _list_companies(
    *,
    page: int,
    per_page: int,
    sector: str | None,
    size: str | None,
    stage: str | None,
    location: str | None,
):
    columns = _company_columns()
    name_sql = _company_name_sql(columns)
    employee_sql = _company_employee_sql(columns)
    location_sql = _company_location_sql(columns)

    where_clauses: list[str] = []
    bind_params: dict[str, object] = {}

    if sector:
        where_clauses.append("LOWER(COALESCE(sector, '')) LIKE :sector")
        bind_params["sector"] = f"%{sector.lower()}%"
    if stage:
        where_clauses.append("LOWER(COALESCE(stage, 'unknown')) = :stage")
        bind_params["stage"] = stage
    if location:
        where_clauses.append(f"LOWER({location_sql}) LIKE :location")
        bind_params["location"] = f"%{location.lower()}%"
    if size:
        min_size, max_size = SIZE_BUCKETS[size]
        where_clauses.append(f"{employee_sql} >= :min_size")
        bind_params["min_size"] = min_size
        if max_size is not None:
            where_clauses.append(f"{employee_sql} <= :max_size")
            bind_params["max_size"] = max_size

    # Always filter out archived companies
    where_clauses.append("archived = FALSE")

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    count_sql = text(f"SELECT COUNT(*) FROM companies {where_sql}")
    total = db.session.execute(count_sql, bind_params).scalar() or 0

    if total == 0:
        return _error_response(
            404,
            "companies_not_found",
            "No companies matched the provided filters.",
            {
                "filters": {
                    "sector": sector,
                    "size": size,
                    "stage": stage,
                    "location": location,
                }
            },
        )

    total_pages = (total + per_page - 1) // per_page
    if page > total_pages:
        return _error_response(
            400,
            "invalid_query_parameter",
            "'page' exceeds available pages for the current query.",
            {
                "field": "page",
                "value": page,
                "total_pages": total_pages,
            },
        )

    select_sql = _build_company_select(columns)
    list_sql = text(f"""
        SELECT {select_sql}
        FROM companies
        {where_sql}
        ORDER BY
            LOWER(COALESCE(sector, 'unknown')) ASC,
            LOWER(COALESCE(stage, 'unknown')) ASC,
            LOWER(COALESCE({name_sql}, '')) ASC,
            id ASC
        LIMIT :limit OFFSET :offset
        """)

    params = {
        **bind_params,
        "limit": per_page,
        "offset": (page - 1) * per_page,
    }
    rows = db.session.execute(list_sql, params).mappings().all()
    companies = [_normalize_company_row(dict(row)) for row in rows]

    return (
        jsonify(
            {
                "items": companies,
                "mindmap": {
                    "levels": ["sector", "stage", "company"],
                    "sectors": _build_mindmap_hierarchy(companies),
                },
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": total_pages,
                },
                "filters": {
                    "sector": sector,
                    "size": size,
                    "stage": stage,
                    "location": location,
                },
            }
        ),
        200,
    )


def _company_photo_gallery(company_id: int) -> list[str]:
    if not _company_media_available():
        return []

    rows = db.session.execute(
        text("""
            SELECT media_url
            FROM company_media
            WHERE company_id = :company_id
            ORDER BY sort_order ASC, id ASC
            """),
        {"company_id": company_id},
    ).mappings()
    return [
        str(row.get("media_url")).strip()
        for row in rows
        if row.get("media_url") and str(row.get("media_url")).strip()
    ]


def _get_company(company_id: int):
    columns = _company_columns()
    select_sql = _build_company_select(columns)

    row = (
        db.session.execute(
            text(f"""
                SELECT {select_sql}
                FROM companies
                WHERE id = :company_id
                LIMIT 1
                """),
            {"company_id": company_id},
        )
        .mappings()
        .first()
    )

    if row is None:
        return _error_response(
            404,
            "company_not_found",
            "Company not found.",
            {"company_id": company_id},
        )

    payload = _normalize_company_row(
        dict(row),
        photo_gallery=_company_photo_gallery(company_id),
    )
    return jsonify({"item": payload}), 200


def register_company_routes(app) -> None:
    @app.get("/companies")
    def list_companies():
        page, error = _parse_positive_int(
            request.args.get("page"), field_name="page", default=DEFAULT_PAGE
        )
        if error:
            return error

        per_page, error = _parse_positive_int(
            request.args.get("per_page"),
            field_name="per_page",
            default=DEFAULT_PER_PAGE,
        )
        if error:
            return error

        if per_page > MAX_COMPANY_PER_PAGE:
            return _error_response(
                400,
                "invalid_query_parameter",
                f"'per_page' must be less than or equal to {MAX_COMPANY_PER_PAGE}.",
                {
                    "field": "per_page",
                    "value": per_page,
                    "max": MAX_COMPANY_PER_PAGE,
                },
            )

        sector = request.args.get("sector")
        size, error = _parse_size_filter(request.args.get("size"))
        if error:
            return error

        stage, error = _parse_enum_filter(
            request.args.get("stage"),
            field_name="stage",
            allowed_values=ALLOWED_STAGE_FILTERS,
        )
        if error:
            return error

        location = request.args.get("location")

        try:
            return _list_companies(
                page=page,
                per_page=per_page,
                sector=sector.strip() if sector else None,
                size=size,
                stage=stage,
                location=location.strip() if location else None,
            )
        except OperationalError:
            return _supabase_list_companies(
                page=page,
                per_page=per_page,
                sector=sector.strip() if sector else None,
                size=size,
                stage=stage,
                location=location.strip() if location else None,
            )

    @app.get("/companies/<int:company_id>")
    def get_company(company_id: int):
        try:
            return _get_company(company_id)
        except OperationalError:
            return _supabase_get_company(company_id)

    @app.post("/companies")
    @require_auth(action="submit_listing")
    def create_company_listing():
        payload, error = _request_json_object()
        if error:
            return error

        try:
            return _create_company_listing(payload)
        except OperationalError:
            db.session.rollback()
            return _error_response(
                503,
                "data_source_unavailable",
                "Could not create company listing due to database connectivity.",
            )

    @app.post("/companies/<int:company_id>/claims")
    @require_auth(action="create_claim")
    def create_company_claim(company_id: int):
        user = g.auth_user

        payload, error = _request_json_object()
        if error:
            return error

        try:
            return _create_claim_request(
                company_id=company_id, payload=payload, user=user
            )
        except OperationalError:
            db.session.rollback()
            return _error_response(
                503,
                "data_source_unavailable",
                "Could not create claim due to database connectivity.",
            )

    @app.get("/companies/<int:company_id>/claims/me")
    @require_auth(action="get_my_claim")
    def get_my_company_claim(company_id: int):
        user = g.auth_user

        try:
            return _user_claim_for_company(company_id=company_id, user=user)
        except OperationalError:
            db.session.rollback()
            return _error_response(
                503,
                "data_source_unavailable",
                "Could not load claim due to database connectivity.",
            )

    @app.get("/admin/claims")
    @require_admin(action="list_claims")
    def list_admin_claims():
        status, error = _parse_enum_filter(
            request.args.get("status"),
            field_name="status",
            allowed_values=CLAIM_STATUS_VALUES,
        )
        if error:
            return error

        try:
            return _list_claim_requests(status=status)
        except OperationalError:
            db.session.rollback()
            return _error_response(
                503,
                "data_source_unavailable",
                "Could not list claims due to database connectivity.",
            )

    @app.patch("/admin/claims/<int:claim_id>/verification")
    @require_admin(action="decide_claim")
    def decide_admin_claim(claim_id: int):
        admin_user = g.auth_user

        payload, error = _request_json_object()
        if error:
            return error

        try:
            return _admin_decide_claim(
                claim_id=claim_id,
                payload=payload,
                admin_user=admin_user,
            )
        except OperationalError:
            db.session.rollback()
            return _error_response(
                503,
                "data_source_unavailable",
                "Could not update claim verification due to database connectivity.",
            )

    @app.patch("/companies/<int:company_id>")
    @require_auth(action="update_company_protected")
    def update_company_protected_fields(company_id: int):
        user = g.auth_user

        payload, error = _request_json_object()
        if error:
            return error

        try:
            return _update_company_protected_fields(
                company_id=company_id,
                payload=payload,
                user=user,
            )
        except OperationalError:
            db.session.rollback()
            return _error_response(
                503,
                "data_source_unavailable",
                "Could not update company due to database connectivity.",
            )
