
from pathlib import Path

import pymupdf

from backend.processing.records import (
    DocumentExtractionResult,
    DocumentRecord,
)


def read_pdf(file_path: str | Path) -> DocumentExtractionResult:
    path = Path(file_path)

    result = DocumentExtractionResult(
        source_filename=path.name,
        source_type="pdf",
    )

    if not path.is_file():
        result.errors.append("File does not exist.")
        return result

    if path.suffix.lower() != ".pdf":
        result.errors.append("Expected a .pdf file.")
        return result

    try:
        with pymupdf.open(path) as document:
            if document.needs_pass:
                result.errors.append("PDF is password-protected.")
                return result

            if len(document) == 0:
                result.errors.append("PDF contains no pages.")
                return result

            for page_index, page in enumerate(document):
                text = page.get_text("text").strip()

                if not text:
                    continue

                result.records.append(
                    DocumentRecord(
                        source_filename=path.name,
                        source_type="pdf",
                        page_number=page_index + 1,
                        raw_fields={"page_text": text},
                    )
                )

            if not result.records:
                result.errors.append(
                    "No extractable text found. "
                    "This PDF may require OCR."
                )

    except Exception as exc:
        result.errors.append(
            f"Could not read PDF: {type(exc).__name__}: {exc}"
        )

    return result
