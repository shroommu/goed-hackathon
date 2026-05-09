from __future__ import annotations

import os

import requests
from flask import Flask, jsonify, request
from sqlalchemy import or_
from sqlalchemy.exc import OperationalError

from .models import Resource

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100
SUPABASE_REST_TIMEOUT_SECONDS = int(os.getenv("SUPABASE_REST_TIMEOUT_SECONDS", "10"))


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
        "archived": "eq.false",
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
        "archived": "eq.false",
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


def register_resource_routes(app: Flask) -> None:
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

        query = Resource.query.filter_by(archived=False)

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
            resource = Resource.query.filter_by(id=resource_id, archived=False).one_or_none()
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
