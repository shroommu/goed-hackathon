from .extensions import db


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column("Title", db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    communities = db.Column("Communities", db.Text, nullable=True)
    industries = db.Column("Industries", db.Text, nullable=True)
    locations = db.Column("Locations", db.Text, nullable=True)
    topics = db.Column("Topics", db.Text, nullable=True)
    link = db.Column(db.Text, nullable=True)
    email = db.Column(db.Text, nullable=True)


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    display_type = db.Column(db.Text, nullable=True)
    linkedin = db.Column(db.Text, nullable=True)
    startup_name = db.Column(db.Text, nullable=True)
    full_address = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    website = db.Column(db.Text, nullable=True)
    stage = db.Column(db.Text, nullable=True)
    employees = db.Column(db.Text, nullable=True)
    sector = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)


class ClaimRequest(db.Model):
    __tablename__ = "claim_requests"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Text, nullable=True)
    submitter_name = db.Column(db.Text, nullable=True)
    submitter_email = db.Column(db.Text, nullable=True)
    status = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=True)
    requested_updates = db.Column(db.JSON, nullable=True)
