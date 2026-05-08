import uuid
from datetime import datetime

from sqlalchemy import UniqueConstraint

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


resource_tags = db.Table(
    "resource_tags",
    db.Column(
        "resource_id",
        db.UUID(as_uuid=True),
        db.ForeignKey("resources.id"),
        primary_key=True,
    ),
    db.Column(
        "tag_id", db.UUID(as_uuid=True), db.ForeignKey("tags.id"), primary_key=True
    ),
)


class Tag(TimestampMixin, db.Model):
    __tablename__ = "tags"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False, unique=True)


class Resource(TimestampMixin, db.Model):
    __tablename__ = "resources"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False, unique=True)
    short_description = db.Column(db.Text, nullable=False)
    official_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    stage = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    objective = db.Column(db.String(120), nullable=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)

    tags = db.relationship(
        "Tag", secondary=resource_tags, lazy="joined", backref="resources"
    )


class FounderProfile(TimestampMixin, db.Model):
    __tablename__ = "founder_profiles"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_label = db.Column(db.String(120), nullable=True)
    stage = db.Column(db.String(50), nullable=False)
    industry = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    objective = db.Column(db.String(120), nullable=False)
    attributes = db.Column(db.JSON, nullable=False, default=dict)


class Recommendation(TimestampMixin, db.Model):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint(
            "founder_profile_id",
            "resource_id",
            name="uq_recommendations_founder_profile_resource",
        ),
    )

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    founder_profile_id = db.Column(
        db.UUID(as_uuid=True), db.ForeignKey("founder_profiles.id"), nullable=False
    )
    resource_id = db.Column(
        db.UUID(as_uuid=True), db.ForeignKey("resources.id"), nullable=False
    )
    score = db.Column(db.Float, nullable=False)
    rationale = db.Column(db.Text, nullable=False)
    rank_position = db.Column(db.Integer, nullable=False)

    founder_profile = db.relationship("FounderProfile", backref="recommendations")
    resource = db.relationship("Resource", backref="recommendations")


class Company(TimestampMixin, db.Model):
    __tablename__ = "companies"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False, unique=True)
    website = db.Column(db.String(500), nullable=False)
    employee_count = db.Column(db.Integer, nullable=True)
    sector = db.Column(db.String(120), nullable=False)
    stage = db.Column(db.String(80), nullable=True)
    year_founded = db.Column(db.Integer, nullable=True)
    linkedin_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=True)
    county = db.Column(db.String(120), nullable=True)
    state = db.Column(db.String(120), nullable=True, default="UT")
    postal_code = db.Column(db.String(30), nullable=True)
    hiring_status = db.Column(db.String(30), nullable=False, default="unknown")
    job_postings = db.Column(db.JSON, nullable=False, default=list)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)


class CompanyMedia(TimestampMixin, db.Model):
    __tablename__ = "company_media"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = db.Column(
        db.UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False
    )
    media_url = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.String(30), nullable=False, default="photo")
    caption = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    company = db.relationship("Company", backref="media")


class CompanyClaim(TimestampMixin, db.Model):
    __tablename__ = "company_claims"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = db.Column(
        db.UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False
    )
    claimant_name = db.Column(db.String(120), nullable=False)
    claimant_email = db.Column(db.String(255), nullable=False)
    claimant_role = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending")
    notes = db.Column(db.Text, nullable=True)

    company = db.relationship("Company", backref="claims")


class VerificationEvent(TimestampMixin, db.Model):
    __tablename__ = "verification_events"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = db.Column(
        db.UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=True
    )
    claim_id = db.Column(
        db.UUID(as_uuid=True), db.ForeignKey("company_claims.id"), nullable=True
    )
    event_type = db.Column(db.String(80), nullable=False)
    outcome = db.Column(db.String(80), nullable=False)
    actor_email = db.Column(db.String(255), nullable=True)
    event_metadata = db.Column(db.JSON, nullable=False, default=dict)

    company = db.relationship("Company", backref="verification_events")
    claim = db.relationship("CompanyClaim", backref="verification_events")
