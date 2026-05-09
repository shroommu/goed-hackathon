from __future__ import annotations

import os
from functools import wraps

from flask import Flask, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from .models import Company, Resource


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


def _require_admin_key(f):
    """Decorator to validate admin API key from Authorization header."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            return _error_response(
                401,
                "missing_authorization",
                "Authorization header is required.",
            )
        
        # Support "Bearer TOKEN" format
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()
        else:
            provided_key = auth_header.strip()
        
        expected_key = os.getenv("ADMIN_API_KEY")
        
        if not expected_key:
            return _error_response(
                503,
                "admin_not_configured",
                "Admin authentication is not configured.",
            )
        
        if provided_key != expected_key:
            return _error_response(
                401,
                "invalid_credentials",
                "Invalid API key.",
            )
        
        return f(*args, **kwargs)
    
    return decorated_function


def _request_json_object():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error_response(
            400,
            "invalid_request_body",
            "Request body must be a JSON object.",
        )
    return payload, None


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
        "archived": resource.archived,
    }


def _company_to_dict(company: Company) -> dict:
    return {
        "id": company.id,
        "display_type": company.display_type,
        "linkedin": company.linkedin,
        "startup_name": company.startup_name,
        "full_address": company.full_address,
        "description": company.description,
        "website": company.website,
        "stage": company.stage,
        "employees": company.employees,
        "sector": company.sector,
        "latitude": company.latitude,
        "longitude": company.longitude,
        "archived": company.archived,
    }


def register_admin_routes(app: Flask) -> None:
    """Register admin-only endpoints for content management."""
    
    @app.post("/admin/resources")
    @_require_admin_key
    def admin_create_resource():
        """Create a new resource."""
        payload, error = _request_json_object()
        if error:
            return error
        
        # Create new resource with provided fields
        resource = Resource()
        
        # Set all fields from payload (optional fields can be None)
        resource.title = payload.get("title")
        resource.description = payload.get("description")
        resource.communities = payload.get("communities")
        resource.industries = payload.get("industries")
        resource.locations = payload.get("locations")
        resource.topics = payload.get("topics")
        resource.link = payload.get("link")
        resource.email = payload.get("email")
        resource.archived = False  # New resources are not archived by default
        
        try:
            db.session.add(resource)
            db.session.commit()
            
            return jsonify({
                "message": "Resource created successfully.",
                "resource": _resource_to_dict(resource),
            }), 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            return _error_response(
                500,
                "database_error",
                "Failed to create resource.",
                {"error": str(e)},
            )
    
    @app.patch("/admin/resources/<int:resource_id>")
    @_require_admin_key
    def admin_update_resource(resource_id: int):
        """Update an existing resource."""
        resource = db.session.get(Resource, resource_id)
        
        if not resource:
            return _error_response(
                404,
                "resource_not_found",
                f"Resource with id {resource_id} not found.",
            )
        
        payload, error = _request_json_object()
        if error:
            return error
        
        # Update all provided fields
        if "title" in payload:
            resource.title = payload["title"]
        if "description" in payload:
            resource.description = payload["description"]
        if "communities" in payload:
            resource.communities = payload["communities"]
        if "industries" in payload:
            resource.industries = payload["industries"]
        if "locations" in payload:
            resource.locations = payload["locations"]
        if "topics" in payload:
            resource.topics = payload["topics"]
        if "link" in payload:
            resource.link = payload["link"]
        if "email" in payload:
            resource.email = payload["email"]
        
        try:
            db.session.commit()
            
            return jsonify({
                "message": "Resource updated successfully.",
                "resource": _resource_to_dict(resource),
            }), 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            return _error_response(
                500,
                "database_error",
                "Failed to update resource.",
                {"error": str(e)},
            )
    
    @app.post("/admin/resources/<int:resource_id>/archive")
    @_require_admin_key
    def admin_archive_resource(resource_id: int):
        """Archive a resource (soft delete)."""
        resource = db.session.get(Resource, resource_id)
        
        if not resource:
            return _error_response(
                404,
                "resource_not_found",
                f"Resource with id {resource_id} not found.",
            )
        
        if resource.archived:
            return _error_response(
                400,
                "already_archived",
                f"Resource with id {resource_id} is already archived.",
            )
        
        resource.archived = True
        
        try:
            db.session.commit()
            
            return jsonify({
                "message": "Resource archived successfully.",
                "resource": _resource_to_dict(resource),
            }), 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            return _error_response(
                500,
                "database_error",
                "Failed to archive resource.",
                {"error": str(e)},
            )
    
    @app.patch("/admin/companies/<int:company_id>")
    @_require_admin_key
    def admin_update_company(company_id: int):
        """Update an existing company."""
        company = db.session.get(Company, company_id)
        
        if not company:
            return _error_response(
                404,
                "company_not_found",
                f"Company with id {company_id} not found.",
            )
        
        payload, error = _request_json_object()
        if error:
            return error
        
        # Update all provided fields
        if "display_type" in payload:
            company.display_type = payload["display_type"]
        if "linkedin" in payload:
            company.linkedin = payload["linkedin"]
        if "startup_name" in payload:
            company.startup_name = payload["startup_name"]
        if "full_address" in payload:
            company.full_address = payload["full_address"]
        if "description" in payload:
            company.description = payload["description"]
        if "website" in payload:
            company.website = payload["website"]
        if "stage" in payload:
            company.stage = payload["stage"]
        if "employees" in payload:
            company.employees = payload["employees"]
        if "sector" in payload:
            company.sector = payload["sector"]
        if "latitude" in payload:
            company.latitude = payload["latitude"]
        if "longitude" in payload:
            company.longitude = payload["longitude"]
        
        try:
            db.session.commit()
            
            return jsonify({
                "message": "Company updated successfully.",
                "company": _company_to_dict(company),
            }), 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            return _error_response(
                500,
                "database_error",
                "Failed to update company.",
                {"error": str(e)},
            )
    
    @app.post("/admin/companies/<int:company_id>/archive")
    @_require_admin_key
    def admin_archive_company(company_id: int):
        """Archive a company (soft delete)."""
        company = db.session.get(Company, company_id)
        
        if not company:
            return _error_response(
                404,
                "company_not_found",
                f"Company with id {company_id} not found.",
            )
        
        if company.archived:
            return _error_response(
                400,
                "already_archived",
                f"Company with id {company_id} is already archived.",
            )
        
        company.archived = True
        
        try:
            db.session.commit()
            
            return jsonify({
                "message": "Company archived successfully.",
                "company": _company_to_dict(company),
            }), 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            return _error_response(
                500,
                "database_error",
                "Failed to archive company.",
                {"error": str(e)},
            )
