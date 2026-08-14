"""
build_dataset.py

Faza 2, kroki 1-4: czyszczenie + chunking + metadane.
Czyta wszystkie pliki JSON z output/arduino_junior (wyniki process_ocr.py),
zapisuje jeden zbiorczy chunks.jsonl gotowy pod embeddingi (Faza 3).

Uruchomienie:
    python build_dataset.py
"""

import json
from pathlib import Path

from text_cleaning import extract_clean_pages, load_ocr_result
from chunking import build_chunks
from lessons_manifest import get_lesson_meta

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

OCR_OUTPUT_DIR = BASE_DIR / "output" / "arduino_junior"
CHUNKS_OUTPUT_PATH = BASE_DIR / "output" / "chunks.jsonl"


def main() -> None:
    json_files = sorted(OCR_OUTPUT_DIR.glob("*.json"))
    print(f"Znaleziono {len(json_files)} plików OCR.")

    all_chunks = []

    for json_path in json_files:
        source_file = json_path.stem
        meta = get_lesson_meta(source_file)

        result = load_ocr_result(json_path)
        pages = extract_clean_pages(result)
        chunks = build_chunks(
            pages=pages,
            subject=meta["subject"],
            lesson_title=meta["lesson_title"],
            source_file=source_file,
        )

        all_chunks.extend(chunks)
        print(f"[OK] {source_file}: {len(pages)} slajdów -> {len(chunks)} chunków")

    CHUNKS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\nZapisano {len(all_chunks)} chunków do {CHUNKS_OUTPUT_PATH}")
    print_length_distribution(all_chunks)


def print_length_distribution(chunks: list[dict]) -> None:
    """Szybki sanity check przed przejściem do Fazy 3."""
    word_counts = sorted(len(c["content"].split()) for c in chunks)
    n = len(word_counts)
    if n == 0:
        return

    print("\n--- Rozkład długości chunków (liczba słów) ---")
    print(f"min: {word_counts[0]}, mediana: {word_counts[n // 2]}, max: {word_counts[-1]}")

    short = [c for c in chunks if len(c["content"].split()) < 15]
    if short:
        print(f"UWAGA: {len(short)} chunków wciąż ma <15 słów mimo mergowania — sprawdź ręcznie:")
        for c in short[:5]:
            preview = c["content"][:60].replace("\n", " ")
            print(f"  - {c['chunk_id']}: \"{preview}...\"")


if __name__ == "__main__":
    main()