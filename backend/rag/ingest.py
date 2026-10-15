
import hashlib
from pathlib import Path

import chromadb
import pymupdf


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GUIDANCE_DIR = PROJECT_ROOT / "data" / "guidance"
DEFAULT_DATABASE_DIR = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "ghg_guidance"


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def create_collection(database_dir: Path = DEFAULT_DATABASE_DIR):
    client = chromadb.PersistentClient(path=str(database_dir))

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Official GHG emissions guidance passages"},
    )


def ingest_pdfs(
    guidance_dir: Path = DEFAULT_GUIDANCE_DIR,
    database_dir: Path = DEFAULT_DATABASE_DIR,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> int:
    guidance_dir = Path(guidance_dir)

    if not guidance_dir.exists():
        raise FileNotFoundError(f"Guidance directory not found: {guidance_dir}")

    pdf_files = sorted(guidance_dir.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {guidance_dir}. "
            "Add official guidance PDFs before ingestion."
        )

    collection = create_collection(Path(database_dir))
    total_chunks = 0

    for pdf_path in pdf_files:
        document = pymupdf.open(str(pdf_path))

        try:
            for page_index, page in enumerate(document):
                page_text = page.get_text("text")
                chunks = chunk_text(page_text, chunk_size, overlap)

                if not chunks:
                    continue

                ids = []
                documents = []
                metadatas = []

                for chunk_index, chunk in enumerate(chunks):
                    unique_value = (
                        f"{pdf_path.name}|{page_index + 1}|"
                        f"{chunk_index}|{chunk}"
                    )
                    chunk_id = hashlib.sha256(
                        unique_value.encode("utf-8")
                    ).hexdigest()

                    ids.append(chunk_id)
                    documents.append(chunk)
                    metadatas.append(
                        {
                            "source_filename": pdf_path.name,
                            "page_number": page_index + 1,
                            "chunk_index": chunk_index,
                        }
                    )

                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )

                total_chunks += len(chunks)

        finally:
            document.close()

        print(f"Processed: {pdf_path.name}")

    print(f"Total chunks processed: {total_chunks}")
    return total_chunks


if __name__ == "__main__":
    ingest_pdfs()
