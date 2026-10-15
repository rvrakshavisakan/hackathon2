# CarbonWise AI

A Django application for uploading emissions activity data, validating rows, calculating CO₂e from supplied values or explicit emission factors, grouping totals by Scope 1, 2, and 3, and exporting CSV reports. Each evaluation is stored against the signed-in user. Uploaded source files are processed in memory and are not retained.

## Requirements

- Windows 10/11
- Python 3.11 or 3.12
- PowerShell

## Setup and run (PowerShell)

```powershell
cd .\CarbonWise_AI_Complete
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in `.env` as `DJANGO_SECRET_KEY=...`. The app reads environment variables directly; load the values in the current PowerShell session before running:

```powershell
$env:DJANGO_SECRET_KEY = 'paste-your-generated-secret-here'
$env:DJANGO_DEBUG = 'true'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
python manage.py migrate
python manage.py createsuperuser
python manage.py check
python manage.py runserver
```

Open http://127.0.0.1:8000/. Sign up, sign in, and upload an activity file. `data/sample/emissions_activity.csv` is a small example. To calculate from activity data, provide `quantity` and `emission_factor` (kg CO₂e per unit). To use already calculated emissions, provide a column named `emissions`, `co2e`, or `CO2e Emissions` (interpreted as kg CO₂e). You may provide `scope` as 1, 2, or 3; if omitted, a simple activity-name heuristic assigns a scope and should be checked by the user. Supported units in report totals are kg CO₂e and t CO₂e.

## Input columns

Recognized activity names include `activity`, `activity type`, `category`, and `emission source`. Activity quantity names include `quantity`, `amount`, `consumption`, and `activity data`. Emission factor names include `emission factor` and `kg co2e per unit`; unit names include `unit`, `units`, `uom`, and `unit of measure`. Rows without an emissions amount or quantity/factor pair are listed as validation issues. Negative, non-finite, or malformed emission values are rejected for that row. At least one valid row is required.

## Database and migrations

SQLite is created as `db.sqlite3` on the first migration. To apply migrations after an update, run `python manage.py migrate`. To create a migration after editing models, run `python manage.py makemigrations` and then `python manage.py migrate`. The database is local runtime data and is excluded from the deliverable.

## Reports and data handling

The results page shows the Scope 1/2/3 totals, per-row calculations, and validation issues. Its CSV report includes the totals and calculated rows. Reports and past evaluations are available only to the owning account. Source upload files are not retained.

The separate document reconciliation API can be started with `uvicorn backend.api.main:app --reload` after installing `requirements.txt`. It accepts CSV, Excel, and PDF evidence through `/api/reconcile`; its local guidance index starts empty unless guidance documents are deliberately ingested. The Django application does not call this API automatically.

## GHG Protocol RAG guidance

Three supplied GHG Protocol PDFs are stored in `data/guidance/`. From the project folder, build or refresh their local Chroma index once with:

```powershell
python -m backend.rag.ingest
```

The first index build may download Chroma's default embedding model and therefore needs internet access. The index is generated under `data/chroma_db/`, excluded from source archives, and can be rebuilt using the command above. Open an evaluation's results page after indexing to see scope-specific review checks and retrieved PDF excerpts with source filenames and page numbers. The suggested checks are deterministic; no LLM-generated recommendations or external API credentials are used. Retrieved passages are contextual evidence, not an automated compliance conclusion. If the index is absent, the rest of the evaluation still works and the page explains how to create it.

## Checks and tests

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The emissions activity calculation uses user-provided emissions or user-provided factors. The included factors registry is only a schema seed and contains no authoritative factors; no factor is silently invented. RAG or external guidance retrieval is not connected to this Django workflow, and this application does not produce an assurance or compliance opinion.
