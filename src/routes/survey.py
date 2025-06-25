from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    get_flashed_messages,
)

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

import random
from datetime import datetime
from models import db, Response, StartupSetAssignment
from utilis import (
    get_unused_story,
    mark_story_as_used,
    generate_news_story_file,
    HOLMES_ARTICLE,
    # CONTROL_ARTICLE,
    CONTROL_FRAUD_ARTICLE,
    # BANKMAN_ARTICLE,
    # generate_startup_file,
    # get_unused_startup,
    # mark_startup_as_used,
    generate_startup_sets,
    mark_startup_set_as_used,
)
from models import db, Response
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
from nltk.corpus import words as nltk_words
import nltk

nltk.download("words")

GERMAN_TZ = ZoneInfo("Europe/Berlin")
import json
import os
import re


survey_bp = Blueprint("survey_bp", __name__)  # Ensure the correct Blueprint name


# @survey_bp.route("/instructions", methods=["GET", "POST"])
# def instructions():
#     if "participant_id" not in session:
#         return redirect(url_for("main.index"))

#     participant_id = session["participant_id"]
#     response = Response.query.filter_by(participant_id=participant_id).first()

#     if request.method == "POST":
#         # No validation needed here if the page is informational
#         response.last_page_viewed = "survey_bp.instructions"
#         db.session.commit()
#         return redirect(url_for("survey_bp.educating"))

#     return render_template("instructions.html")


@survey_bp.route("/instructions", methods=["GET", "POST"])
def instructions():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    # # Time tracking for this attempt
    # attempt_start = session.get(
    #         "instruction_start", datetime.now(GERMAN_TZ).timestamp()
    #     )
    # attempt_duration = datetime.now(GERMAN_TZ).timestamp() - attempt_start

    # session["instruction_duration"] = (
    #         session.get("instruction_duration", 0) + attempt_duration
    #     )

    if request.method == "POST":

        start_time = session.get(
            "instruction_start", datetime.now(GERMAN_TZ).timestamp()
        )
        now = datetime.now(GERMAN_TZ).timestamp()
        attempt_duration = now - start_time

        session["instruction_duration"] = (
            session.get("instruction_duration", 0) + attempt_duration
        )
        session["instruction_start"] = now
        selected = request.form.getlist("answer")
        # response.instructions_answer = json.dumps(selected)
        # response.last_page_viewed = "survey_bp.instructions"
        # db.session.commit()
        # db.session.refresh(response)

        # return redirect(url_for("survey_bp.information"))

        # ✅ Backend validation of checkboxes
        if set(selected) == {"Agree", "Others"} and len(selected) == 2:
            response.last_page_viewed = "survey_bp.instructions"
            response.instruction_duration = session.pop("instruction_duration", 0)

            db.session.commit()
            db.session.refresh(response)  # ✅ Ensure the session reflects the DB write

            return redirect(url_for("survey_bp.educating"))
        else:
            flash("Incorrect answer. Please read the question again.", "error")
            return redirect(url_for("survey_bp.instructions"))
    session["instruction_start"] = datetime.now(GERMAN_TZ).timestamp()
    return render_template("instructions.html")


# @survey_bp.route("/educating", methods=["GET", "POST"])
# def educating():
#     if "participant_id" not in session:
#         return redirect(url_for("main.index"))

#     participant_id = session["participant_id"]
#     response = Response.query.filter_by(participant_id=participant_id).first()

#     if request.method == "POST":
#         response.last_page_viewed = "survey_bp.educating"
#         db.session.commit()
#         return redirect(url_for("survey_bp.phase_control"))

#     return render_template("educating.html")


@survey_bp.route("/educating", methods=["GET", "POST"])
def educating():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        prospect_answer = request.form.get("prospect")
        investor_answer = request.form.get("investors")

        if prospect_answer == "out_of_business" and investor_answer == "both":
            response.last_page_viewed = "survey_bp.educating"
            db.session.commit()
            db.session.refresh(response)  # ✅ Ensure the session reflects the DB write

            return redirect(url_for("survey_bp.phase_control"))
        else:
            flash("Incorrect answer. Please read the content and try again.", "error")
            return redirect(url_for("survey_bp.educating"))

    return render_template("educating.html")


# @survey_bp.route("/phase_control", methods=["GET", "POST"])
# def phase_control():
#     if "participant_id" not in session:
#         return redirect(url_for("main.index"))

#     participant_id = session["participant_id"]
#     response = Response.query.filter_by(participant_id=participant_id).first()

#     if request.method == "POST":
#         response.last_page_viewed = "survey_bp.phase_control"
#         db.session.commit()
#         return redirect(url_for("survey_bp.news_info"))

#     return render_template("phase_control.html")


@survey_bp.route("/phase_control", methods=["GET", "POST"])
def phase_control():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        selected = request.form.get("phase_response")
        if selected == "read_news":
            response.last_page_viewed = "survey_bp.phase_control"
            db.session.commit()
            db.session.refresh(response)  # ✅ Ensure the session reflects the DB write

            return redirect(url_for("survey_bp.news_info"))
        else:
            flash("Incorrect answer. Please read the prompt and try again.", "error")
            return redirect(url_for("survey_bp.phase_control"))

    return render_template("phase_control.html")


@survey_bp.route("/news_info", methods=["GET", "POST"])
def news_info():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    generate_news_story_file()

    if request.method == "POST":
        start_time = session.get(
            "news_info_start_time", datetime.now(GERMAN_TZ).timestamp()
        )
        now = datetime.now(GERMAN_TZ).timestamp()
        attempt_duration = now - start_time

        session["news_info_duration_total"] = (
            session.get("news_info_duration_total", 0) + attempt_duration
        )
        session["news_info_start_time"] = now  # Reset start time for next attempt
        user_answer = request.form.get("news_answer")
        story_type = request.form.get("story_type")
        unique_code = request.form.get("unique_code")

        if not user_answer:
            flash("Please select an answer before proceeding.", "error")
            return redirect(url_for("survey_bp.news_info"))

        # Load article based on story_type to get the correct answer
        # article_data = HOLMES_ARTICLE if story_type == "holmes" else CONTROL_ARTICLE
        if story_type == "holmes":
            article_data = HOLMES_ARTICLE
        else:
            article_data = CONTROL_FRAUD_ARTICLE

        correct_answer = article_data["correct_answer"]

        is_correct = user_answer == correct_answer

        if not is_correct:
            flash("Incorrect answer. Try again.", "error")
            return redirect(url_for("survey_bp.news_info"))

        mark_story_as_used(unique_code)

        response.unique_code = unique_code
        response.story_type = story_type
        response.user_answer = user_answer
        response.is_correct = is_correct
        response.last_page_viewed = "survey_bp.news_info"
        response.news_info_duration = session.pop(
            "news_info_duration_total", 0
        )  # Save total duration

        db.session.commit()
        get_flashed_messages()  # <--- THIS clears any old messages BEFORE redirect
        session.pop("story_entry", None)

        return redirect(url_for("survey_bp.investment"))

    # === GET method ===
    story_entry = session.get("story_entry")

    if not story_entry:
        story_entry = get_unused_story()
        if not story_entry:
            flash("All available stories have been used. Survey is closed.", "error")
            return redirect(url_for("main.index"))
        session["story_entry"] = story_entry  # Save to session for reuse

    # article_data = (
    #     HOLMES_ARTICLE if story_entry["story"] == "holmes" else CONTROL_ARTICLE
    # )

    session["news_info_start_time"] = datetime.now(GERMAN_TZ).timestamp()
    article_data = (
        HOLMES_ARTICLE
        if story_entry["story"] == "holmes"
        else CONTROL_FRAUD_ARTICLE
        # else (
        #     BANKMAN_ARTICLE
        #     if story_entry["story"] == "bankman"
        #     else CONTROL_FRAUD_ARTICLE
        # )
    )
    correct_answer = article_data["correct_answer"]
    shuffled_options = article_data["options"].copy()
    # random.shuffle(shuffled_options)

    # Determine image filename
    image_filename = "holmes.png" if story_entry["story"] == "holmes" else "control_fraud.png"
    # image_filename = (
    #     "holmes.png"
    #     if story_entry["story"] == "holmes"
    #     else (
    #         "control.png"
    #         if story_entry["story"] == "control_news"
    #         else "control_fraud.png"
    #     )
    # )

    return render_template(
        "news_info.html",
        news_title=article_data["title"],
        news_content=article_data["content"],
        news_source=article_data["source"],
        question=article_data["question"],
        options=shuffled_options,
        unique_code=story_entry["code"],
        story_type=story_entry["story"],
        correct_answer=correct_answer,
        image_filename=image_filename,  # send image file to template
    )


@survey_bp.route("/investment", methods=["GET", "POST"])
def investment():
    print("Debug: participant_id in session:", session.get("participant_id"))

    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    STARTUP_JSON_PATH = "startup_data.json"

    # === POST: process investment inputs ===
    if request.method == "POST":
        current_page = session.get("startup_page", 0)
        all_startups = session.get("startups")
        partial_investments = session.get("partial_investments", {})

        if not all_startups or current_page is None:
            flash("Session expired. Please restart the task.", "error")
            return redirect(url_for("main.index"))

        page_startups = all_startups[current_page * 2 : current_page * 2 + 2]

        for startup in page_startups:
            name = startup["Startup_name"]
            field_name = f"investment_{name}"
            amount_str = request.form.get(field_name)

            if amount_str is None:
                flash("Missing investment amount.", "error")
                return render_template("investment_multi.html", startups=page_startups, page=current_page)

            try:
                amount = int(round(float(amount_str)))
            except (ValueError, TypeError):
                flash("Invalid amount.", "error")
                return render_template("investment_multi.html", startups=page_startups, page=current_page)

            if not (0 <= amount <= 300000):
                flash("Each amount must be between 0 and 300,000.", "error")
                return render_template("investment_multi.html", startups=page_startups, page=current_page)

            partial_investments[name] = amount

        # Update session
        session["partial_investments"] = partial_investments

        if current_page < 2:
            session["startup_page"] = current_page + 1
            return redirect(url_for("survey_bp.investment"))  # go to next page
        else:
            # Final page: validate total and save to DB
            total = sum(partial_investments.values())
            if total != 300000:
                flash(
                    f"Total must be $300,000. You entered ${total:,}.",
                    "error"
                )
                return render_template("investment_multi.html", startups=page_startups, page=current_page)

            # Save response to DB
            response = Response.query.filter_by(participant_id=participant_id).first()
            if response:
                response.startup_code = session.get("startup_set_code")
                response.startup_info = all_startups
                response.startup_investments = partial_investments
                response.startup_investment_duration = (
                    datetime.now(GERMAN_TZ).timestamp() - session["startup_set_start_time"]
                )
                db.session.commit()

            # Mark set as used, clean up
            assignment = StartupSetAssignment.query.filter_by(
                startup_set_code=session["startup_set_code"]
            ).first()
            if assignment:
                assignment.used = True
                db.session.commit()

            mark_startup_set_as_used(session["startup_set_code"])

            for key in ["startups", "startup_page", "startup_set_code", "startup_set_start_time", "partial_investments"]:
                session.pop(key, None)

            return redirect(url_for("survey_bp.investment_approach"))

    # === GET: show form ===
    if "startups" not in session:
        # Load new startup set
        with open(STARTUP_JSON_PATH, "r") as file:
            startup_data = json.load(file)

        unused_sets = [item for item in startup_data if not item["used"]]

        if not unused_sets:
            flash("No unused startup sets available.", "error")
            return redirect(url_for("main.index"))

        # selected_set = unused_sets[0]
        selected_set = random.choice(unused_sets)
        session["startups"] = selected_set["startups"]
        session["startup_set_code"] = selected_set["code"]
        session["startup_set_start_time"] = datetime.now(GERMAN_TZ).timestamp()
        session["startup_page"] = 0
        session["partial_investments"] = {}

        selected_set["used"] = True  # temporary flag only
        with open(STARTUP_JSON_PATH, "w") as file:
            json.dump(startup_data, file)

        # Create or update assignment
        assignment = StartupSetAssignment.query.filter_by(
            participant_id=participant_id
        ).first()
        if not assignment:
            assignment = StartupSetAssignment(
                participant_id=participant_id,
                startup_set_code=selected_set["code"],
                used=True,
                duration_seconds=None,
            )
            db.session.add(assignment)
        else:
            assignment.startup_set_code = selected_set["code"]
            assignment.used = True
            assignment.duration_seconds = None
        db.session.commit()

    # else: session already has the set (retry after failed POST)
    all_startups = session["startups"]
    page = session.get("startup_page", 0)
    page_startups = all_startups[page * 2 : page * 2 + 2]

    print("Debug: session['startup_set_code']:", session.get("startup_set_code"))
    print("Debug: session['startups']:", all_startups)
    print(
        "Debug: session['startup_set_start_time']:",
        session.get("startup_set_start_time"),
    )

    return render_template("investment_multi.html", startups=page_startups, page=page)


ENGLISH_WORDS = set(nltk_words.words())


def is_english_word(word):
    return word.lower() in ENGLISH_WORDS


ALLOWED_CHARS_PATTERN = re.compile(r"^[a-zA-Z0-9’'“”\"(),.:;!?-]+$")


def is_gibberish(text):
    words = [w for w in text.strip().split() if w]
    if len(words) < 10:
        return True

    mostly_short = sum(1 for w in words if len(w) < 3) / len(words) > 0.3
    unique_ratio = len(set(w.lower() for w in words)) / len(words)
    too_repetitive = unique_ratio < 0.6
    non_alpha = (
        sum(1 for w in words if not ALLOWED_CHARS_PATTERN.fullmatch(w)) / len(words)
        > 0.2
    )

    # New: how many words aren't in the dictionary
    unknown_words = sum(1 for w in words if not is_english_word(w))
    unknown_ratio = unknown_words / len(words)

    return mostly_short or too_repetitive or non_alpha or unknown_ratio > 0.4


@survey_bp.route("/investment_approach", methods=["GET", "POST"])
def investment_approach():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        approach_text = request.form.get("investment_approach", "").strip()

        if (
            not approach_text
            or len(approach_text.split()) < 10
            or is_gibberish(approach_text)
        ):
            error = "Please write at least 10 meaningful words to describe your investment approach."
            return render_template(
                "investment_approach.html",
                error=error,
                investment_approach=approach_text,
            )

        response.investment_approach = approach_text
        response.last_page_viewed = "survey_bp.investment_approach"
        db.session.commit()

        return redirect(
            url_for("survey_bp.investment_reflect_likert")
        )  # Replace with your next route

    return render_template("investment_approach.html")


@survey_bp.route("/investment_reflect_likert", methods=["GET", "POST"])
def investment_reflect_likert():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        keys = [
            "industry_rating",
            "product_rating",
            "maturity_rating",
            "experience_rating",
            "innovativeness_rating",
            "integrity_rating",
        ]

        likert_data = {}
        for key in keys:
            val = request.form.get(key)
            if not val:
                flash(f"Missing response for: {key.replace('_', ' ').title()}", "error")
                return redirect(url_for("survey_bp.investment_reflect_likert"))
            likert_data[key] = int(val)

        response.likert_reflection = likert_data  # Optional if column is Text
        response.last_page_viewed = "survey_bp.investment_reflect_likert"
        db.session.commit()

        return redirect(url_for("survey_bp.investment_demographic"))  # Or next step

    return render_template("investment_reflect_likert.html")


@survey_bp.route("/demographic_collecting", methods=["GET", "POST"])
def investment_demographic():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        gender = request.form.get("gender")
        gender_other = request.form.get("gender_other") if gender == "Other" else None

        age = request.form.get("age")

        education = request.form.get("education")
        education_other = (
            request.form.get("education_other") if education == "Other" else None
        )

        guess_intention = request.form.get("guess_intention", "").strip()

        if not gender or not age or not education:
            flash("Please complete all fields before submitting.", "error")
            return redirect(url_for("survey_bp.investment_demographic"))

        # if gender == "Other" and not gender_other:
        #     flash("Please specify your gender.", "error")
        #     return redirect(url_for("survey_bp.investment_demographic"))

        # if education == "Other" and not education_other:
        #     flash("Please specify your education level.", "error")
        #     return redirect(url_for("survey_bp.investment_demographic"))

        try:
            age_val = int(age)
            if age_val < 10 or age_val > 120:
                flash("Please enter a valid age between 10 and 120.", "error")
                return redirect(url_for("survey_bp.investment_demographic"))
        except ValueError:
            flash("Age must be a number.", "error")
            return redirect(url_for("survey_bp.investment_demographic"))

        response.gender = gender
        response.age = age_val
        response.education_level = education
        response.guess_intention = guess_intention
        response.last_page_viewed = "survey_bp.investment_demographic"
        db.session.commit()

        return redirect(url_for("survey_bp.final_page"))

    return render_template("demographic.html")


@survey_bp.route("/final_page", methods=["GET", "POST"])
def final_page():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    # if not response or not response.unique_code or not response.startup_code:
    #     flash("Missing completion code data.", "error")
    #     return redirect(url_for("main.index"))
    # Get startup code from StartupSetAssignment instead of response.startup_code
    assignment = StartupSetAssignment.query.filter_by(
        participant_id=participant_id
    ).first()

    if (
        not response
        or not response.unique_code
        or not assignment
        or not assignment.startup_set_code
    ):
        flash("Missing completion code data.", "error")
        return redirect(url_for("main.index"))

    expected_code = f"{response.unique_code}{assignment.startup_set_code}"

    if request.method == "POST":
        mturk_id = request.form.get("mturk_id", "").strip()
        user_code = request.form.get("completion_code", "").strip().upper()
        feedback = request.form.get("survey_feedback", "").strip()  # <-- New line

        # if not mturk_id or not user_code:
        if not user_code:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("survey_bp.final_page"))

        if user_code != expected_code:
            flash(
                "The code you entered is incorrect. Please check and try again.",
                "error",
            )
            return redirect(url_for("survey_bp.final_page"))

        # Save to DB
        # response.mturk_id = mturk_id
        response.completion_code = user_code
        response.survey_feedback = feedback
        response.last_page_viewed = "survey_bp.final_page"
        db.session.commit()

        # Store for thank-you page
        session["completion_code"] = user_code
        # session["mturk_id"] = mturk_id

        return redirect(url_for("survey_bp.thank_you"))

    return render_template("final_page.html", expected_code=expected_code)


@survey_bp.route("/thank_you")
def thank_you():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if response.total_time_survey_minutes is None:
        end = datetime.now(GERMAN_TZ)
        response.end_time = end

        if response.start_time.tzinfo is None:
            response.start_time = response.start_time.replace(tzinfo=GERMAN_TZ)
        duration = (end - response.start_time).total_seconds() / 60
        response.total_time_survey_minutes = round(duration, 2)
        response.last_page_viewed = "survey_bp.thank_you"
        response.completed = True
        db.session.commit()

    # mturk_id = session.get("mturk_id", "")
    completion_code = session.get("completion_code", "")

    return render_template(
        # "thank_you.html", mturk_id=mturk_id, completion_code=completion_code
        "thank_you.html",
        prolific_id=session.get("prolific_id"),
        completion_code=completion_code,
    )
