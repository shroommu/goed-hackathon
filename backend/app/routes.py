from flask import Flask, current_app, jsonify


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
