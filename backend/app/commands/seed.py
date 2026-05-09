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


def _row_get(row: dict, *keys: str) -> str | list | None:
    for key in keys:
        if key in row:
            return row.get(key)

    lowered = {str(key).lower(): value for key, value in row.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value is not None:
            return value
    return None


def _normalize_text(value: str | list | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        joined = "; ".join([str(item).strip() for item in value if str(item).strip()])
        return joined or None
    text = str(value).strip()
    return text or None


def _resource_payload_from_row(row: dict) -> dict:
    title = _normalize_text(_row_get(row, "name", "title", "Title"))
    if not title:
        raise ValueError("missing required title/name")

    description = _normalize_text(_row_get(row, "short_description", "description"))
    link = _normalize_text(_row_get(row, "official_url", "link"))
    email = _normalize_text(_row_get(row, "email", "Email"))

    communities = _parse_list_field(_row_get(row, "communities", "Communities", "tags"))
    industries = _parse_list_field(
        _row_get(row, "industries", "Industries", "category")
    )
    locations = _parse_list_field(_row_get(row, "locations", "Locations", "location"))
    topics = _parse_list_field(_row_get(row, "topics", "Topics", "objective", "tags"))

    return {
        "title": title,
        "description": description,
        "link": link,
        "email": email,
        "communities": "; ".join(communities) or None,
        "industries": "; ".join(industries) or None,
        "locations": "; ".join(locations) or None,
        "topics": "; ".join(topics) or None,
    }


def _resource_changed(resource: Resource, payload: dict) -> bool:
    return any(
        [
            resource.description != payload["description"],
            resource.link != payload["link"],
            resource.email != payload["email"],
            resource.communities != payload["communities"],
            resource.industries != payload["industries"],
            resource.locations != payload["locations"],
            resource.topics != payload["topics"],
        ]
    )


def _upsert_resource_payload(payload: dict) -> tuple[str, Resource]:
    normalized_title = payload["title"].casefold()
    resource = Resource.query.filter(
        func.lower(Resource.title) == normalized_title
    ).one_or_none()

    if resource is None:
        resource = Resource(id=_next_resource_id(), title=payload["title"])
        db.session.add(resource)
        action = "created"
    else:
        action = "updated" if _resource_changed(resource, payload) else "unchanged"

    resource.description = payload["description"]
    resource.link = payload["link"]
    resource.email = payload["email"]
    resource.communities = payload["communities"]
    resource.industries = payload["industries"]
    resource.locations = payload["locations"]
    resource.topics = payload["topics"]

    return action, resource


def _build_resource_query(
    communities: str | None,
    industries: str | None,
    locations: str | None,
    topics: str | None,
):
    query = Resource.query
    if communities:
        query = query.filter(Resource.communities.ilike(f"%{communities.strip()}%"))
    if industries:
        query = query.filter(Resource.industries.ilike(f"%{industries.strip()}%"))
    if locations:
        query = query.filter(Resource.locations.ilike(f"%{locations.strip()}%"))
    if topics:
        query = query.filter(Resource.topics.ilike(f"%{topics.strip()}%"))
    return query


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
    @app.cli.command("import-resources")
    @click.option(
        "--file",
        "resources_path",
        required=True,
        help="Path to resources import file (JSON or CSV).",
    )
    @click.option(
        "--report",
        "report_path",
        default=None,
        help="Optional path to write a JSON ingestion report.",
    )
    @click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Validate and simulate import without persisting changes.",
    )
    def import_resources(
        resources_path: str, report_path: str | None, dry_run: bool
    ) -> None:
        resources_file = Path(resources_path)
        if not resources_file.exists():
            raise click.ClickException(f"Resources file not found: {resources_file}")

        rows = _parse_rows(resources_file)
        created = 0
        updated = 0
        unchanged = 0
        invalid = 0
        errors: list[dict] = []

        for index, row in enumerate(rows, start=1):
            try:
                with db.session.begin_nested():
                    payload = _resource_payload_from_row(row)
                    action, _ = _upsert_resource_payload(payload)
                    db.session.flush()

                if action == "created":
                    created += 1
                elif action == "updated":
                    updated += 1
                else:
                    unchanged += 1
            except Exception as exc:  # noqa: BLE001
                invalid += 1
                errors.append(
                    {
                        "row": index,
                        "error": str(exc),
                        "title": _normalize_text(
                            _row_get(row, "name", "title", "Title")
                        ),
                    }
                )

        if dry_run:
            db.session.rollback()
        else:
            db.session.commit()

        report = {
            "file": str(resources_file),
            "dry_run": dry_run,
            "rows_total": len(rows),
            "created": created,
            "updated": updated,
            "unchanged": unchanged,
            "invalid": invalid,
            "errors": errors,
        }

        if report_path:
            output_file = Path(report_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

        click.echo(
            "Import complete. "
            f"rows_total={report['rows_total']}, "
            f"created={created}, updated={updated}, unchanged={unchanged}, invalid={invalid}"
        )

        if errors:
            click.echo("Row-level validation errors:")
            for item in errors:
                click.echo(
                    f"  - row={item['row']}, title={item['title'] or '<missing>'}: {item['error']}"
                )

    @app.cli.command("query-resources")
    @click.option("--communities", default=None, help="Filter by Communities field.")
    @click.option("--industries", default=None, help="Filter by Industries field.")
    @click.option("--locations", default=None, help="Filter by Locations field.")
    @click.option("--topics", default=None, help="Filter by Topics field.")
    @click.option("--limit", default=20, show_default=True, help="Max rows to display.")
    def query_resources(
        communities: str | None,
        industries: str | None,
        locations: str | None,
        topics: str | None,
        limit: int,
    ) -> None:
        query = _build_resource_query(communities, industries, locations, topics)
        rows = query.order_by(Resource.id.asc()).limit(limit).all()

        click.echo(f"Matched {len(rows)} resource(s).")
        for resource in rows:
            click.echo(
                f"  - id={resource.id}, title={resource.title}, "
                f"communities={resource.communities or '-'}, "
                f"industries={resource.industries or '-'}, "
                f"locations={resource.locations or '-'}, "
                f"topics={resource.topics or '-'}"
            )

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
