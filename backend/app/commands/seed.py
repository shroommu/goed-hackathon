import csv
import json
from pathlib import Path

import click
from flask import Flask
from sqlalchemy import func

from app.extensions import db
from app.models import Company, Resource


def _next_resource_id() -> int:
    max_id = db.session.query(func.max(Resource.id)).scalar()
    return int(max_id or 0) + 1


def _parse_rows(file_path: Path) -> list[dict]:
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        with file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return payload if isinstance(payload, list) else payload.get("items", [])

    if suffix == ".csv":
        with file_path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    raise click.ClickException(f"Unsupported file type: {file_path.suffix}")


def _parse_list_field(value: str | list | None, separator: str = ";") -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []
    # Support both semicolon and comma delimited values from CSV exports.
    if ";" not in value and "," in value:
        separator = ","
    return [item.strip() for item in value.split(separator) if item.strip()]


def _upsert_resource(row: dict) -> Resource:
    title = (row.get("name") or row.get("title") or "").strip()
    if not title:
        raise click.ClickException("Resource row missing required 'name' or 'title'")

    resource = Resource.query.filter_by(title=title).one_or_none()
    if resource is None:
        resource = Resource(id=_next_resource_id(), title=title)
        db.session.add(resource)

    resource.description = (
        row.get("short_description")
        or row.get("description")
        or resource.description
        or ""
    ).strip()
    resource.link = (row.get("official_url") or row.get("link") or "").strip() or None
    resource.email = (row.get("email") or "").strip() or None

    communities = _parse_list_field(row.get("communities") or row.get("tags"))
    industries = _parse_list_field(row.get("industries") or row.get("category"))
    locations = _parse_list_field(row.get("locations") or row.get("location"))
    topics = _parse_list_field(
        row.get("topics") or row.get("objective") or row.get("tags")
    )

    resource.communities = "; ".join(communities) or None
    resource.industries = "; ".join(industries) or None
    resource.locations = "; ".join(locations) or None
    resource.topics = "; ".join(topics) or None

    return resource


def _upsert_company(row: dict) -> Company:
    startup_name = (row.get("name") or row.get("startup_name") or "").strip()
    if not startup_name:
        raise click.ClickException(
            "Company row missing required 'name' or 'startup_name'"
        )

    company = Company.query.filter_by(startup_name=startup_name).one_or_none()
    if company is None:
        company = Company(startup_name=startup_name)
        db.session.add(company)

    company.display_type = (row.get("display_type") or "startup").strip() or None
    company.linkedin = (
        row.get("linkedin_url") or row.get("linkedin") or ""
    ).strip() or None
    company.website = (row.get("website") or "").strip()
    company.employees = (
        str(row.get("employee_count") or row.get("employees") or "").strip() or None
    )
    company.sector = (row.get("sector") or "Unknown").strip()
    company.stage = row.get("stage") or None
    company.description = (row.get("description") or "").strip()

    full_address = (row.get("full_address") or "").strip()
    if not full_address:
        address_parts = [
            (row.get("address") or "").strip(),
            (row.get("city") or "").strip(),
            (row.get("state") or "").strip(),
            (row.get("postal_code") or "").strip(),
        ]
        full_address = ", ".join([part for part in address_parts if part])
    company.full_address = full_address or None

    company.latitude = float(row["latitude"]) if row.get("latitude") else None
    company.longitude = float(row["longitude"]) if row.get("longitude") else None

    return company


def register_seed_command(app: Flask) -> None:
    @app.cli.command("seed-starter-data")
    @click.option(
        "--resources",
        "resources_path",
        default="data/starter/resources_starter.json",
        show_default=True,
        help="Path to resources starter pack (JSON or CSV).",
    )
    @click.option(
        "--companies",
        "companies_path",
        default="data/starter/companies_starter.json",
        show_default=True,
        help="Path to companies starter pack (JSON or CSV).",
    )
    def seed_starter_data(resources_path: str, companies_path: str) -> None:
        resources_file = Path(resources_path)
        companies_file = Path(companies_path)

        if not resources_file.exists():
            raise click.ClickException(f"Resources file not found: {resources_file}")
        if not companies_file.exists():
            raise click.ClickException(f"Companies file not found: {companies_file}")

        resources_rows = _parse_rows(resources_file)
        companies_rows = _parse_rows(companies_file)

        created_or_updated_resources = 0
        created_or_updated_companies = 0

        for row in resources_rows:
            _upsert_resource(row)
            created_or_updated_resources += 1

        for row in companies_rows:
            _upsert_company(row)
            created_or_updated_companies += 1

        db.session.commit()

        click.echo(
            f"Seed complete. resources={created_or_updated_resources}, "
            f"companies={created_or_updated_companies}"
        )
