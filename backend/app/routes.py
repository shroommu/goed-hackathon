from __future__ import annotations

from flask import Blueprint, Flask, current_app, jsonify

from .routes_admin import register_admin_routes
from .routes_companies import register_company_routes
from .routes_navigator import register_navigator_routes
from .routes_resources import register_resource_routes


def register_routes(app: Flask) -> None:
    # Create a blueprint for all API routes with /api prefix
    api = Blueprint("api", __name__, url_prefix="/api")

    @api.get("/health")
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
    
    @api.get("/navigator/debug")
    def navigator_debug():
        """Debug endpoint to check navigator configuration"""
        from .models import Resource
        from .routes_navigator import get_llm_client
        
        debug_info = {
            "openrouter_api_key_configured": bool(current_app.config.get("OPENROUTER_API_KEY")),
            "openrouter_model": current_app.config.get("OPENROUTER_MODEL", "not set"),
            "database_url_configured": bool(current_app.config.get("SQLALCHEMY_DATABASE_URI")),
        }
        
        # Test database connection
        try:
            resource_count = Resource.query.filter_by(archived=False).count()
            debug_info["database_connection"] = "ok"
            debug_info["resource_count"] = resource_count
        except Exception as e:
            debug_info["database_connection"] = "failed"
            debug_info["database_error"] = str(e)
        
        # Test LLM client
        try:
            llm_client = get_llm_client()
            debug_info["llm_client"] = "configured" if llm_client else "not configured"
        except Exception as e:
            debug_info["llm_client"] = "error"
            debug_info["llm_error"] = str(e)
        
        return jsonify(debug_info), 200

    register_resource_routes(api)
    register_company_routes(api)
    register_admin_routes(api)
    register_navigator_routes(api)

    # Register the blueprint with the app
    app.register_blueprint(api)


__all__ = ["register_routes"]
