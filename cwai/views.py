import csv
import io
import math
from pathlib import Path

import pandas as pd
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Evaluation
from .guidance import retrieve_evaluation_guidance

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
SCOPE_ALIASES = {"1": "scope1", "scope 1": "scope1", "scope1": "scope1", "2": "scope2", "scope 2": "scope2", "scope2": "scope2", "3": "scope3", "scope 3": "scope3", "scope3": "scope3"}


def _key(value):
    return " ".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())


def _find(row, *names):
    normalized = {_key(column): value for column, value in row.items()}
    for name in names:
        if _key(name) in normalized:
            return normalized[_key(name)]
    return None


def _infer_scope(activity):
    activity = _key(activity or "")
    if any(word in activity for word in ("electricity", "grid power", "steam", "heating", "cooling")):
        return "scope2"
    if any(word in activity for word in ("fuel", "vehicle", "combustion", "furnace", "process", "refrigerant")):
        return "scope1"
    return "scope3"


def _read_upload(upload):
    raw = upload.read()
    if Path(upload.name).suffix.lower() == ".csv":
        return pd.read_csv(io.BytesIO(raw)).to_dict(orient="records")
    return pd.read_excel(io.BytesIO(raw)).to_dict(orient="records")


def _calculate_rows(records):
    if not records:
        raise ValueError("The uploaded file contains no data rows.")
    totals = {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0}
    rows, issues = [], []
    for number, source in enumerate(records, start=2):
        activity = _find(source, "activity", "activity type", "category", "emission source", "source")
        value = _find(source, "emissions_value", "emissions", "co2e", "co2e emissions", "carbon emissions", "total emissions")
        quantity = _find(source, "quantity", "amount", "consumption", "activity data", "activity quantity", "value")
        factor = _find(source, "emission factor", "emission_factor", "kg co2e per unit", "kg_co2e_per_unit")
        try:
            if value is not None and not pd.isna(value):
                kg = float(value)
            elif quantity is not None and factor is not None and not pd.isna(quantity) and not pd.isna(factor):
                kg = float(quantity) * float(factor)
            else:
                issues.append(f"Row {number}: provide an emissions value or both quantity and emission factor.")
                continue
            if not math.isfinite(kg) or kg < 0:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            issues.append(f"Row {number}: emissions must be a finite, non-negative number.")
            continue
        scope_value = _find(source, "scope", "ghg scope")
        missing_scope = scope_value is None or (isinstance(scope_value, float) and pd.isna(scope_value))
        scope = _infer_scope(activity) if missing_scope else SCOPE_ALIASES.get(_key(scope_value))
        if scope is None:
            issues.append(f"Row {number}: scope must be 1, 2, or 3.")
            continue
        kg = float(kg)
        tonnes = kg / 1000
        totals[scope] += tonnes
        unit = _find(source, "unit", "units", "uom", "unit of measure")
        unit = "" if unit is None or (isinstance(unit, float) and pd.isna(unit)) else str(unit)
        rows.append({"row": number, "activity": str(activity or "Unspecified activity"), "scope": scope, "emissions_kg": round(kg, 6), "emissions_tonnes": round(tonnes, 6), "unit": unit})
    if not rows:
        raise ValueError("No valid emissions rows were found. Add an emissions/CO2e column, or quantity and emission factor columns.")
    return totals, rows, issues


def login_view(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", "").strip(), password=request.POST.get("password", ""))
        if user:
            login(request, user)
            return redirect("home")
        messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def signup_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1, password2 = request.POST.get("password1", ""), request.POST.get("password2", "")
        error = None
        if not full_name or not username or not password1 or not password2:
            error = "Please fill in all required fields."
        elif password1 != password2:
            error = "Passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = "This username already exists. Choose another."
        elif len(password1) < 8:
            error = "Password must contain at least 8 characters."
        if error:
            return render(request, "signup.html", {"error": error})
        User.objects.create_user(username=username, email=email, password=password1, first_name=full_name)
        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")
    return render(request, "signup.html")


@login_required(login_url="login")
def home_view(request):
    evaluations = Evaluation.objects.filter(user=request.user)[:10]
    return render(request, "home.html", {"evaluations": evaluations})


@login_required(login_url="login")
@require_POST
def analyze_view(request):
    upload = request.FILES.get("excel_file")
    if not upload:
        messages.error(request, "Please upload a CSV or Excel file.")
        return redirect("home")
    if Path(upload.name).suffix.lower() not in {".csv", ".xlsx", ".xls"}:
        messages.error(request, "Upload a CSV or Excel file (.csv, .xlsx, .xls).")
        return redirect("home")
    if upload.size > MAX_UPLOAD_BYTES:
        messages.error(request, "The upload exceeds the 25 MB limit.")
        return redirect("home")
    try:
        target = float(request.POST.get("expected_emission", ""))
        if not math.isfinite(target) or target < 0:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Enter a valid non-negative emissions target.")
        return redirect("home")
    try:
        totals, rows, issues = _calculate_rows(_read_upload(upload))
        evaluation = Evaluation.objects.create(user=request.user, filename=Path(upload.name).name[:255], expected_emission=target, total_emission=sum(totals.values()), scope1_emission=totals["scope1"], scope2_emission=totals["scope2"], scope3_emission=totals["scope3"], rows=rows, validation_issues=issues)
        request.session["evaluation_id"] = evaluation.pk
        return redirect("results")
    except Exception as exc:
        messages.error(request, f"Could not process the file: {exc}")
        return redirect("home")


@login_required(login_url="login")
def loading_view(request):
    return redirect("results")


@login_required(login_url="login")
def results_view(request):
    evaluation = Evaluation.objects.filter(pk=request.session.get("evaluation_id"), user=request.user).first()
    if evaluation is None:
        messages.info(request, "Run an evaluation to view results.")
        return redirect("home")
    guidance = retrieve_evaluation_guidance(evaluation)
    context = {"evaluation": evaluation, "calculated_emission": round(evaluation.total_emission, 6), "expected_emission": evaluation.expected_emission, "comparison_status": "Within expected target" if evaluation.total_emission <= evaluation.expected_emission else "Above expected target", "scope1_emission": round(evaluation.scope1_emission, 6), "scope2_emission": round(evaluation.scope2_emission, 6), "scope3_emission": round(evaluation.scope3_emission, 6), "guidance": guidance}
    return render(request, "results.html", context)


@login_required(login_url="login")
def report_view(request, evaluation_id):
    evaluation = Evaluation.objects.filter(pk=evaluation_id, user=request.user).first()
    if evaluation is None:
        raise Http404
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="carbonwise-evaluation-{evaluation.pk}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Source file", evaluation.filename])
    writer.writerow(["Created", evaluation.created_at.isoformat()])
    writer.writerow(["Scope", "Emissions (tCO2e)"])
    for scope, total in (("Scope 1", evaluation.scope1_emission), ("Scope 2", evaluation.scope2_emission), ("Scope 3", evaluation.scope3_emission)):
        writer.writerow([scope, total])
    writer.writerow(["Total", evaluation.total_emission])
    writer.writerow(["Target", evaluation.expected_emission])
    writer.writerow([])
    writer.writerow(["Row", "Activity", "Scope", "Emissions (kgCO2e)", "Emissions (tCO2e)", "Unit"])
    for row in evaluation.rows:
        writer.writerow([row["row"], row["activity"], row["scope"], row["emissions_kg"], row["emissions_tonnes"], row["unit"]])
    if evaluation.validation_issues:
        writer.writerow([])
        writer.writerow(["Validation issues"])
        writer.writerows([[issue] for issue in evaluation.validation_issues])
    return response


@login_required(login_url="login")
def logout_view(request):
    logout(request)
    return redirect("login")
