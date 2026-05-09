from __future__ import annotations

import os
import re

import requests
from flask import Flask, current_app, jsonify, request
from sqlalchemy import or_, text
from sqlalchemy.exc import OperationalError

from .models import Resource
from .extensions import db

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100
MAX_COMPANY_PER_PAGE = 100
SUPABASE_REST_TIMEOUT_SECONDS = int(os.getenv("SUPABASE_REST_TIMEOUT_SECONDS", "10"))

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


def _resource_to_dict(resource: Resource) -> dict:
    return {
        "id": resource.id,
        "title": resource.title,
        "description": resource.description,
        "communities": resource.communities,
        "industries": resource.industries,
        "locations": resource.locations,
        "topics": resource.topics,
        "link": resource.link,
        "email": resource.email,
    }


def _resource_from_supabase_row(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "title": row.get("title") or row.get("Title"),
        "description": row.get("description"),
        "communities": row.get("communities") or row.get("Communities"),
        "industries": row.get("industries") or row.get("Industries"),
        "locations": row.get("locations") or row.get("Locations"),
        "topics": row.get("topics") or row.get("Topics"),
        "link": row.get("link"),
        "email": row.get("email"),
    }


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


def _supabase_list_resources(
    *,
    page: int,
    per_page: int,
    communities: str | None,
    industries: str | None,
    locations: str | None,
    topics: str | None,
    search: str | None,
):
    headers, error = _supabase_request_headers()
    if error:
        return error

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    endpoint = f"{supabase_url}/rest/v1/resources"

    params: dict[str, str | int] = {
        "select": "id,Title,description,Communities,Industries,Locations,Topics,link,email",
        "order": "id.asc",
        "limit": per_page,
        "offset": (page - 1) * per_page,
    }

    if communities:
        params["Communities"] = f"ilike.*{communities.strip()}*"
    if industries:
        params["Industries"] = f"ilike.*{industries.strip()}*"
    if locations:
        params["Locations"] = f"ilike.*{locations.strip()}*"
    if topics:
        params["Topics"] = f"ilike.*{topics.strip()}*"
    if search:
        search_term = search.strip()
        params["or"] = (
            f"(Title.ilike.*{search_term}*,"
            f"description.ilike.*{search_term}*,"
            f"Communities.ilike.*{search_term}*,"
            f"Industries.ilike.*{search_term}*,"
            f"Locations.ilike.*{search_term}*,"
            f"Topics.ilike.*{search_term}*)"
        )

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
    total = _supabase_count_from_content_range(
        response.headers.get("content-range"),
        len(rows),
    )

    return (
        jsonify(
            {
                "items": [_resource_from_supabase_row(row) for row in rows],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total else 0,
                },
                "filters": {
                    "communities": communities,
                    "industries": industries,
                    "locations": locations,
                    "topics": topics,
                    "search": search,
                },
            }
        ),
        200,
    )


def _supabase_get_resource(resource_id: int):
    headers, error = _supabase_request_headers()
    if error:
        return error

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    endpoint = f"{supabase_url}/rest/v1/resources"
    params = {
        "select": "id,Title,description,Communities,Industries,Locations,Topics,link,email",
        "id": f"eq.{resource_id}",
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
            "resource_not_found",
            "Resource not found.",
            {"resource_id": resource_id},
        )

    return jsonify({"item": _resource_from_supabase_row(rows[0])}), 200


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


def register_routes(app: Flask) -> None:
    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return (
            jsonify(
                {
                    "status": "ok",
                    "build_version": current_app.config.get("BUILD_VERSION", "unknown"),
                    "environment": current_app.config.get("APP_ENV", "unknown"),
                }
            ),
            200,
        )

    @app.get("/resources")
    def list_resources():
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

        if per_page > MAX_PER_PAGE:
            return _error_response(
                400,
                "invalid_query_parameter",
                f"'per_page' must be less than or equal to {MAX_PER_PAGE}.",
                {"field": "per_page", "value": per_page, "max": MAX_PER_PAGE},
            )

        communities = request.args.get("communities")
        industries = request.args.get("industries")
        locations = request.args.get("locations")
        topics = request.args.get("topics")
        search = request.args.get("search")

        query = Resource.query

        if communities:
            query = query.filter(Resource.communities.ilike(f"%{communities.strip()}%"))
        if industries:
            query = query.filter(Resource.industries.ilike(f"%{industries.strip()}%"))
        if locations:
            query = query.filter(Resource.locations.ilike(f"%{locations.strip()}%"))
        if topics:
            query = query.filter(Resource.topics.ilike(f"%{topics.strip()}%"))
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Resource.title.ilike(term),
                    Resource.description.ilike(term),
                    Resource.communities.ilike(term),
                    Resource.industries.ilike(term),
                    Resource.locations.ilike(term),
                    Resource.topics.ilike(term),
                )
            )

        try:
            total = query.count()
            rows = (
                query.order_by(Resource.id.asc())
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )
        except OperationalError:
            return _supabase_list_resources(
                page=page,
                per_page=per_page,
                communities=communities,
                industries=industries,
                locations=locations,
                topics=topics,
                search=search,
            )

        return (
            jsonify(
                {
                    "items": [_resource_to_dict(resource) for resource in rows],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "total_pages": (
                            (total + per_page - 1) // per_page if total else 0
                        ),
                    },
                    "filters": {
                        "communities": communities,
                        "industries": industries,
                        "locations": locations,
                        "topics": topics,
                        "search": search,
                    },
                }
            ),
            200,
        )

    @app.get("/resources/<int:resource_id>")
    def get_resource(resource_id: int):
        try:
            resource = Resource.query.filter_by(id=resource_id).one_or_none()
        except OperationalError:
            return _supabase_get_resource(resource_id)

        if resource is None:
            return _error_response(
                404,
                "resource_not_found",
                "Resource not found.",
                {"resource_id": resource_id},
            )

        return jsonify({"item": _resource_to_dict(resource)}), 200

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
