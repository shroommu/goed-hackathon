import csv
import json
from pathlib import Path

import click
from flask import Flask

from app.extensions import db
from app.models import Company, CompanyMedia, Resource, Tag


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
    return [item.strip() for item in value.split(separator) if item.strip()]


def _upsert_resource(row: dict) -> Resource:
    name = (row.get("name") or "").strip()
    if not name:
        raise click.ClickException("Resource row missing required 'name'")

    resource = Resource.query.filter_by(name=name).one_or_none()
    if resource is None:
        resource = Resource(name=name)
        db.session.add(resource)

    resource.short_description = (row.get("short_description") or "").strip()
    resource.official_url = (row.get("official_url") or "").strip()
    resource.category = (row.get("category") or "General").strip()
    resource.stage = row.get("stage") or None
    resource.location = row.get("location") or None
    resource.objective = row.get("objective") or None
    resource.is_archived = str(row.get("is_archived", "false")).lower() == "true"

    tag_names = _parse_list_field(row.get("tags"))
    resource.tags = []
    for tag_name in tag_names:
        tag = Tag.query.filter_by(name=tag_name).one_or_none()
        if tag is None:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        resource.tags.append(tag)

    return resource


def _upsert_company(row: dict) -> Company:
    name = (row.get("name") or "").strip()
    if not name:
        raise click.ClickException("Company row missing required 'name'")

    company = Company.query.filter_by(name=name).one_or_none()
    if company is None:
        company = Company(name=name)
        db.session.add(company)

    company.website = (row.get("website") or "").strip()
    company.employee_count = (
        int(row["employee_count"]) if row.get("employee_count") else None
    )
    company.sector = (row.get("sector") or "Unknown").strip()
    company.stage = row.get("stage") or None
    company.year_founded = int(row["year_founded"]) if row.get("year_founded") else None
    company.linkedin_url = row.get("linkedin_url") or None
    company.description = (row.get("description") or "").strip()
    company.address = (row.get("address") or "").strip()
    company.city = row.get("city") or None
    company.county = row.get("county") or None
    company.state = row.get("state") or "UT"
    company.postal_code = row.get("postal_code") or None
    company.hiring_status = row.get("hiring_status") or "unknown"

    company.latitude = float(row["latitude"]) if row.get("latitude") else None
    company.longitude = float(row["longitude"]) if row.get("longitude") else None

    job_postings = row.get("job_postings", [])
    if isinstance(job_postings, str):
        job_postings = _parse_list_field(job_postings)
    company.job_postings = job_postings

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
            company = _upsert_company(row)
            gallery_items = _parse_list_field(row.get("photo_gallery"))
            if gallery_items:
                company.media.clear()
                for idx, media_url in enumerate(gallery_items):
                    company.media.append(
                        CompanyMedia(
                            media_url=media_url,
                            media_type="photo",
                            sort_order=idx,
                        )
                    )
            created_or_updated_companies += 1

        db.session.commit()

        click.echo(
            f"Seed complete. resources={created_or_updated_resources}, "
            f"companies={created_or_updated_companies}"
        )
