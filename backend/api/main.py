from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.pipeline import run_pipeline
from backend.processing.pdf_reader import read_pdf
from backend.processing.readers import read_csv, read_excel

app = FastAPI(
    title="CarbonWise AI",
    description=(
        "Carbon emissions reconciliation and evidence review. "
        "Findings require human review and are not compliance verdicts."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024


def _extract_file(file_path: Path):
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return read_csv(file_path)

    if suffix in {".xlsx", ".xls"}:
        return read_excel(file_path)

    if suffix == ".pdf":
        return read_pdf(file_path)

    raise ValueError("Unsupported file extension.")


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    total_bytes = 0

    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                total_bytes += len(chunk)

                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"{upload.filename} exceeds the 20 MB limit.",
                    )

                output.write(chunk)
    finally:
        await upload.close()

    if total_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail=f"{upload.filename} is empty.",
        )


@app.get("/health")
def health():
    return {"status": "ok", "service": "CarbonWise AI"}


@app.post("/api/reconcile")
async def reconcile_documents(
    reported_file: UploadFile = File(...),
    evidence_files: list[UploadFile] = File(...),
    required_evidence: str = Form(""),
    value_field: str = Form("quantity"),
):
    if value_field not in {"quantity", "emissions_value"}:
        raise HTTPException(
            status_code=422,
            detail="value_field must be quantity or emissions_value.",
        )

    uploads = [reported_file, *evidence_files]

    for upload in uploads:
        if not upload.filename:
            raise HTTPException(status_code=400, detail="A filename is missing.")

        if Path(upload.filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {upload.filename}",
            )

    try:
        with TemporaryDirectory(prefix="carbonwise-") as temporary_directory:
            temporary_path = Path(temporary_directory)
            extracted = []

            for index, upload in enumerate(uploads):
                safe_name = Path(upload.filename).name
                destination = temporary_path / f"{index}_{safe_name}"

                await _save_upload(upload, destination)
                result = _extract_file(destination)

                result.source_filename = safe_name
                for record in result.records:
                    record.source_filename = safe_name

                extracted.append(result)

            categories = [
                category.strip().lower()
                for category in required_evidence.split(",")
                if category.strip()
            ]

            return run_pipeline(
                reported_extraction=extracted[0],
                evidence_extractions=extracted[1:],
                required_evidence=categories,
                value_field=value_field,
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {type(exc).__name__}",
        ) from exc
