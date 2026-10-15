
from pathlib import Path

from backend.rag.ingest import (
    DEFAULT_DATABASE_DIR,
    create_collection,
)


def search_guidance(
    query: str,
    n_results: int = 4,
    database_dir: Path = DEFAULT_DATABASE_DIR,
    max_distance: float | None = None,
) -> list[dict]:
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    if n_results <= 0:
        raise ValueError("n_results must be greater than zero")

    if max_distance is not None and max_distance < 0:
        raise ValueError("max_distance cannot be negative")

    collection = create_collection(Path(database_dir))
    collection_size = collection.count()

    if collection_size == 0:
        return []

    results = collection.query(
        query_texts=[query.strip()],
        n_results=min(n_results, collection_size),
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    seen_passages = set()

    documents = results["documents"][0] or []
    metadatas = results["metadatas"][0] or []
    distances = results["distances"][0] or []

    for document, metadata, distance in zip(
        documents, metadatas, distances
    ):
        if not document or not metadata:
            continue

        if max_distance is not None and distance > max_distance:
            continue

        normalized_text = " ".join(document.lower().split())
        passage_key = (
            metadata.get("source_filename"),
            metadata.get("page_number"),
            normalized_text,
        )

        if passage_key in seen_passages:
            continue

        seen_passages.add(passage_key)

        matches.append(
            {
                "text": document,
                "source_filename": metadata.get("source_filename"),
                "page_number": metadata.get("page_number"),
                "chunk_index": metadata.get("chunk_index"),
                "distance": float(distance),
            }
        )

    return matches


if __name__ == "__main__":
    question = input("What emissions guidance do you want to find? ")

    for match in search_guidance(question):
        print(f"\nSource: {match['source_filename']}")
        print(f"Page: {match['page_number']}")
        print(f"Distance: {match['distance']:.4f}")
        print(match["text"])
