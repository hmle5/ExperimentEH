from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    send_file,
)
from models import db, Response
import pandas as pd
import io
from flask import Response as FlaskResponse
from functools import wraps
import statistics

admin_bp = Blueprint("admin_bp", __name__)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            flash("Unauthorized access! Please log in as admin.", "error")
            return redirect(url_for("admin_bp.admin_login"))
        return func(*args, **kwargs)

    return wrapper


# @admin_bp.route("/admin", methods=["GET"])
# @admin_required
# def admin_dashboard():
#     page = int(request.args.get("page", 1))
#     per_page = int(request.args.get("per_page", 10))

#     paginated = Response.query.paginate(page=page, per_page=per_page, error_out=False)
#     all_responses = Response.query.all()

#     durations = [
#         (r.end_time - r.start_time).total_seconds() / 60
#         for r in all_responses
#         if r.start_time and r.end_time
#     ]
#     avg_duration = round(statistics.mean(durations), 2) if durations else None
#     total_completed = sum(1 for r in all_responses if r.completed)

#     def serialize_response(r):
#         return {
#             "participant_id": r.participant_id,
#             "completed": r.completed,
#             "start_time": r.start_time.isoformat() if r.start_time else None,
#             "end_time": r.end_time.isoformat() if r.end_time else None,
#             "investment_duration": r.startup_investment_duration,
#             "age": r.age,
#             "gender": r.gender,
#         }

#     serialized_responses = [serialize_response(r) for r in paginated.items]

#     return render_template(
#         "admin_dashboard.html",
#         responses=paginated.items,
#         serialized_responses=serialized_responses,
#         page=page,
#         per_page=per_page,
#         total=paginated.total,
#         avg_duration=avg_duration,
#         total_completed=total_completed,
#     )


@admin_bp.route("/admin", methods=["GET"])
@admin_required
def admin_dashboard():
    from sqlalchemy import and_

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    gender_filter = request.args.get("gender")
    education_filter = request.args.get("education_level")

    filters = []
    if gender_filter:
        filters.append(Response.gender == gender_filter)
    if education_filter:
        filters.append(Response.education_level == education_filter)

    query = Response.query.filter(and_(*filters)) if filters else Response.query
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    all_responses = query.all()

    # Summary stats
    durations = [
        (r.end_time - r.start_time).total_seconds() / 60
        for r in all_responses
        if r.start_time and r.end_time
    ]
    avg_duration = round(statistics.mean(durations), 2) if durations else None
    total_completed = sum(1 for r in all_responses if r.completed)

    # Charts: avg duration by gender
    from collections import defaultdict

    duration_by_gender = defaultdict(list)
    for r in all_responses:
        if r.gender and r.start_time and r.end_time:
            duration = (r.end_time - r.start_time).total_seconds() / 60
            duration_by_gender[r.gender].append(duration)

    avg_duration_by_gender = {
        g: round(statistics.mean(d), 2) for g, d in duration_by_gender.items()
    }

    return render_template(
        "admin_dashboard.html",
        responses=paginated.items,
        page=page,
        per_page=per_page,
        total=paginated.total,
        avg_duration=avg_duration,
        total_completed=total_completed,
        avg_duration_by_gender=avg_duration_by_gender,
        selected_gender=gender_filter,
        selected_education=education_filter,
    )


@admin_bp.route("/admin/export_excel", methods=["GET"])
@admin_required
def export_excel():
    responses = Response.query.all()
    data = [
        {
            "participant_ID": r.participant_id,
            "prolific_ID": r.prolific_id,
            "completed": r.completed,
            "completion_code": r.completion_code,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "total_time": r.total_time_survey_minutes,
            "attention_check1": r.attentioncheck_1_response,
            "attention_check1_duration": r.attentioncheck_1_duration,
            "attention_check2": r.instructions_answer,
            "attention_check2_duration": r.instruction_duration,
            "news": r.story_type,
            "news_info_duration": r.news_info_duration,
            "investment_duration": r.startup_investment_duration,
            "startup_set_code": r.startup_code,
            "startup_set_info": r.startup_info,
            "startup_investments": r.startup_investments,
            "investment_approach": r.investment_approach,
            "likert_reflection": r.likert_reflection,
            "age": r.age,
            "gender": r.gender,
            "education": r.education_level,
            "guess_intention": r.guess_intention,
            "survey_feedback": r.survey_feedback,
        }
        for r in responses
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Responses")
    output.seek(0)

    return send_file(
        output,
        download_name="survey_responses.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@admin_bp.route("/admin/export_csv", methods=["GET"])
@admin_required
def export_csv():
    responses = Response.query.all()
    data = [
        {
            "participant_ID": r.participant_id,
            "prolific_ID": r.prolific_id,
            "completed": r.completed,
            "completion_code": r.completion_code,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "total_time": r.total_time_survey_minutes,
            "attention_check1": r.attentioncheck_1_response,
            "attention_check1_duration": r.attentioncheck_1_duration,
            "attention_check2": r.instructions_answer,
            "attention_check2_duration": r.instruction_duration,
            "news": r.story_type,
            "news_info_duration": r.news_info_duration,
            "investment_duration": r.startup_investment_duration,
            "startup_set_code": r.startup_code,
            "startup_set_info": r.startup_info,
            "startup_investments": r.startup_investments,
            "investment_approach": r.investment_approach,
            "likert_reflection": r.likert_reflection,
            "age": r.age,
            "gender": r.gender,
            "education": r.education_level,
            "guess_intention": r.guess_intention,
            "survey_feedback": r.survey_feedback,
        }
        for r in responses
    ]

    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return FlaskResponse(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=survey_responses.csv"},
    )


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "securepassword":
            session["admin"] = True
            return redirect(url_for("admin_bp.admin_dashboard"))
        else:
            flash("Invalid credentials!", "error")

    return render_template("admin_login.html")


@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_bp.admin_login"))