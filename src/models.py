from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo

GERMAN_TZ = ZoneInfo("Europe/Berlin")
import json

db = SQLAlchemy()


class UserConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consent_id = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(200), nullable=False)
    consent_given = db.Column(db.Boolean, default=False, nullable=False)
    date_given = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(GERMAN_TZ)
    )

    # date_given = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consent_id = db.Column(
        db.String(100),
        db.ForeignKey("user_consent.consent_id"),
        nullable=False,
        unique=True,
    )
    participant_id = db.Column(db.String(100), unique=True, nullable=False)
    unique_code = db.Column(db.String(50), unique=True, nullable=True)
    story_type = db.Column(db.String(20), nullable=True)  # Track which story was shown
    user_answer = db.Column(db.String(300), nullable=True)  # User's answer
    is_correct = db.Column(db.Boolean, nullable=True)  # Whether the answer was correct
    completed = db.Column(db.Boolean, default=False, nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    total_time_survey_minutes = db.Column(
        db.Float, nullable=True
    )  # Total duration in minutes
    date_created = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(GERMAN_TZ)
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(GERMAN_TZ),
        onupdate=lambda: datetime.now(GERMAN_TZ),
    )
    startup_code = db.Column(db.String(50), nullable=True)
    # founder_name = db.Column(db.String(100), nullable=True)
    # failure_prob = db.Column(db.Float, nullable=True)
    # success_prob = db.Column(db.Float, nullable=True)
    # expected_return = db.Column(db.Float, nullable=True)
    # voyagemind_investment = db.Column(db.Float, nullable=True)
    # voyagemind_dollar_return = db.Column(db.Float, nullable=True)
    # startup_factors = db.Column(db.String(300), nullable=True)
    # founder_factors = db.Column(db.String(300), nullable=True)
    attentioncheck_1_duration = db.Column(
        db.Float, nullable=True
    )  # Duration in seconds
    attentioncheck_1_response = db.Column(db.Text, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    education_level = db.Column(db.String(50), nullable=True)
    prolific_id = db.Column(db.String(100), nullable=True)
    completion_code = db.Column(db.String(50), nullable=True)
    last_page_viewed = db.Column(db.String(100), nullable=True)

    # New fields to track investments and time spent
    startup_investments = db.Column(
        db.JSON, nullable=True
    )  # Store the investment amounts as JSON
    startup_investment_duration = db.Column(
        db.Float, nullable=True
    )  # Store the time spent during investment

    # New field to collect free-text approach answer
    investment_approach = db.Column(db.Text, nullable=True)

    # New field to collect likert reflection answer
    likert_reflection = db.Column(db.JSON, nullable=True)

    # Relationship for easy access to UserConsent
    user_consent = db.relationship("UserConsent", backref="responses")

    # Index for faster queries
    __table_args__ = (db.Index("idx_response_consent_id", "consent_id"),)

    # Survey feedback
    survey_feedback = db.Column(db.Text, nullable=True)


class StartupSetAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.String(100), nullable=False, index=True)
    startup_set_code = db.Column(db.String(10), nullable=False, unique=True)
    # assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime, default=lambda: datetime.now(GERMAN_TZ))
    duration_seconds = db.Column(db.Float, nullable=True)
    used = db.Column(db.Boolean, default=False, nullable=False)
    # date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    date_created = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(GERMAN_TZ)
    )
