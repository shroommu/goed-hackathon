from __future__ import annotations

from flask import Flask, current_app, jsonify

from .routes_admin import register_admin_routes
from .routes_companies import register_company_routes, requests
from .routes_resources import register_resource_routes


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

    register_resource_routes(app)
    register_company_routes(app)
    register_admin_routes(app)


__all__ = ["register_routes", "requests"]
