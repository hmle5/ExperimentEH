from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import uuid
import re
import time
from zoneinfo import ZoneInfo


from datetime import datetime
from collections import Counter
from nltk.corpus import words as nltk_words
import nltk

nltk.download("words")

from models import db, UserConsent, Response
from utilis import get_client_ip, get_user_agent, generate_unique_participant_id

GERMAN_TZ = ZoneInfo("Europe/Berlin")
# import logging
# from flask import Flask, request, render_template
# from flask_session import Session
# from flask_session_captcha import FlaskSessionCaptcha

main_bp = Blueprint("main", __name__)


@main_bp.route("/consent", methods=["GET"])
def consent():
    # ip = get_client_ip()
    # user_agent = get_user_agent()
    # consent_record = UserConsent.query.filter_by(
    #     ip_address=ip, user_agent=user_agent
    # ).first()

    consent_id = session.get("consent_id")
    if consent_id:
        consent_record = UserConsent.query.filter_by(consent_id=consent_id).first()
        if consent_record and consent_record.consent_given:
            return redirect(url_for("main.index"))

    return render_template("consent.html")


@main_bp.route("/give_consent", methods=["POST"])
def give_consent():
    """Processes user consent."""
    consent_status = request.form.get("consent")
    if consent_status == "accepted":
        ip = get_client_ip()
        user_agent = get_user_agent()
        consent_id = str(uuid.uuid4())

        consent_record = UserConsent(
            consent_id=consent_id,
            ip_address=ip,
            user_agent=user_agent,
            consent_given=True,
        )
        db.session.add(consent_record)
        db.session.commit()

        session["consent_id"] = consent_id
        return redirect(url_for("main.attentioncheck_1"))  # Proceed to index
    elif consent_status == "denied":
        return redirect(url_for("main.exit"))  # Redirect to exit page
    else:
        flash("Please select an option to proceed.")
        return redirect(url_for("main.consent"))


@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


# Exit page
@main_bp.route("/exit", methods=["GET", "POST"])
def exit():
    return render_template("exit.html")


# @main_bp.route("/attentioncheck_1", methods=["GET", "POST"])
# def attentioncheck_1():
#     error = None
#     if request.method == "POST":
#         response_text = request.form.get("response", "").strip()
#         word_count = len([w for w in response_text.split() if w.strip()])

#         if word_count < 15:
#             error = "Please enter at least 15 words."
#         else:
#             return redirect(url_for("main.index"))

#     return render_template("attentioncheck_1.html", error=error)

ENGLISH_WORDS = set(nltk_words.words())


def is_english_word(word):
    return word.lower() in ENGLISH_WORDS


def is_gibberish(text):
    words = [w for w in text.strip().split() if w]
    if len(words) < 15:
        return True

    mostly_short = sum(1 for w in words if len(w) < 3) / len(words) > 0.3
    unique_ratio = len(set(w.lower() for w in words)) / len(words)
    too_repetitive = unique_ratio < 0.6
    non_alpha = (
        sum(1 for w in words if not re.fullmatch(r"[a-zA-Z]+", w)) / len(words) > 0.2
    )

    # New: how many words aren't in the dictionary
    unknown_words = sum(1 for w in words if not is_english_word(w))
    unknown_ratio = unknown_words / len(words)

    return mostly_short or too_repetitive or non_alpha or unknown_ratio > 0.4


def is_too_fast(min_seconds=5):
    now_ts = datetime.now(GERMAN_TZ).timestamp()
    return now_ts - session.get("start_time", 0) < min_seconds


@main_bp.route("/attentioncheck_1", methods=["GET", "POST"])
def attentioncheck_1():
    error = None

    if request.method == "POST":
        response_text = request.form.get("response", "").strip()
        honeypot = request.form.get("website", "")

        # Time tracking for this attempt
        attempt_start = session.get(
            "attention_attempt_start", datetime.now(GERMAN_TZ).timestamp()
        )
        attempt_duration = datetime.now(GERMAN_TZ).timestamp() - attempt_start

        session["attentioncheck_1_duration"] = (
            session.get("attentioncheck_1_duration", 0) + attempt_duration
        )

        if honeypot:
            error = "Invalid submission."
        elif is_too_fast():
            error = "Please take more time to consider your answer."
        elif is_gibberish(response_text):
            error = "Your response appears repetitive or nonsensical. Please provide a real opinion with at least 15 meaningful words."
        else:
            # Passed the check
            session["attentioncheck_1_response"] = response_text

            consent_id = session.get("consent_id")
            response_record = Response.query.filter_by(consent_id=consent_id).first()

            if response_record:
                response_record.attentioncheck_1_response = response_text
                response_record.attentioncheck_1_duration = session.get(
                    "attentioncheck_1_duration", 0
                )
                db.session.commit()

            return redirect(url_for("main.index"))

    if request.method == "GET":
        if "start_time" not in session:
            session["start_time"] = datetime.now(GERMAN_TZ).timestamp()

        session["attention_attempt_start"] = datetime.now(GERMAN_TZ).timestamp()

    return render_template("attentioncheck_1.html", error=error)


@main_bp.route("/index", methods=["GET", "POST"])
def index():
    error = None
    consent_id = session.get("consent_id")

    # Validate that user has given consent
    consent_record = UserConsent.query.filter_by(consent_id=consent_id).first()
    if not consent_record or not consent_record.consent_given:
        return redirect(url_for("main.consent"))

    # Check if this user has a response already
    response_record = Response.query.filter_by(consent_id=consent_id).first()

    if response_record:
        # Set session info from DB
        session["participant_id"] = response_record.participant_id
        # session["start_time"] = response_record.start_time.isoformat()
        session["start_time"] = response_record.start_time.timestamp()
        session["question_answered"] = True

        if response_record.completed:
            return render_template("already_completed.html")

        # Resume from the next step in survey flow
        SURVEY_FLOW = [
            "survey_bp.instructions",
            "survey_bp.educating",
            "survey_bp.phase_control",
            "survey_bp.news_info",
            "survey_bp.investment",
            "survey_bp.investment_approach",
            "survey_bp.investment_reflect_likert",
            "survey_bp.investment_demographic",
            "survey_bp.final_page",
            "survey_bp.thank_you",
        ]

        last_page = response_record.last_page_viewed or SURVEY_FLOW[0]
        try:
            last_index = SURVEY_FLOW.index(last_page)
            next_step = SURVEY_FLOW[min(last_index + 1, len(SURVEY_FLOW) - 1)]
        except ValueError:
            next_step = SURVEY_FLOW[0]

        return redirect(url_for(next_step))

    # Handle new participant form submission
    if request.method == "POST":
        prolific_id = request.form.get("prolific_id", "").strip()
        if not prolific_id:
            error = "Please enter your Prolific ID before continuing."
            return render_template("index.html", error=error)

        # ❗ Check for duplicate Prolific ID (across all users)
        existing_prolific = Response.query.filter_by(prolific_id=prolific_id).first()
        if existing_prolific:
            return render_template("already_completed.html")

        # Create new response record
        participant_id = uuid.uuid4().hex
        session["participant_id"] = participant_id
        session["start_time"] = session.get(
            "start_time", datetime.now(GERMAN_TZ).timestamp()
        )

        # session["start_time"] = session.get("start_time", time.time())  # fallback
        session["question_answered"] = True
        session["prolific_id"] = prolific_id

        try:
            response_record = Response(
                consent_id=consent_id,
                participant_id=participant_id,
                prolific_id=prolific_id,
                completed=False,
                start_time=datetime.fromtimestamp(
                    float(session["start_time"]), GERMAN_TZ
                ),
                attentioncheck_1_duration=session.get("attentioncheck_1_duration"),
                attentioncheck_1_response=session.get("attentioncheck_1_response"),
            )
            db.session.add(response_record)
            db.session.commit()
            db.session.refresh(response_record)
        except Exception as e:
            db.session.rollback()
            error = "Database error occurred. Please try again later."
            print("DB error:", e)
            return render_template("index.html", error=error)

        return redirect(url_for("survey_bp.instructions"))

    return render_template("index.html", error=error)
