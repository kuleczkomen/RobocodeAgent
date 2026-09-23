"""
build_dataset.py

Faza 2, kroki 1-4: czyszczenie + chunking + metadane.
Czyta wszystkie pliki JSON z output/arduino_junior (wyniki process_ocr.py),
automatycznie dociąga (z cache'em) opisy obrazków wyłuskane przez
image_extraction.py i zapisuje jeden zbiorczy chunks.jsonl gotowy pod
embeddingi (Faza 3).

Uruchomienie:
    python data_preparation/build_dataset.py
    flaga --debug-images wypisuje opisy obrazków
"""

import json
import re
from pathlib import Path
import argparse

from text_cleaning import extract_clean_pages, load_ocr_result
from chunking import build_chunks, MIN_WORDS_PER_CHUNK
from lessons_manifest import get_lesson_meta
from utils.output_path import get_output_path
from image_extraction import get_image_descriptions

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
SUBJECT_NAME = "arduino_junior"

OCR_OUTPUT_DIR = BASE_DIR / "output" / SUBJECT_NAME
PDF_INPUT_DIR = BASE_DIR / "dataset" / SUBJECT_NAME
IMAGES_CACHE_DIR = BASE_DIR / "output" / "images" / SUBJECT_NAME
CHUNKS_OUTPUT_BASE_PATH = BASE_DIR / "output" / "chunks" / f"{SUBJECT_NAME}.jsonl"
CHUNKS_OUTPUT_PATH = get_output_path(CHUNKS_OUTPUT_BASE_PATH)


def merge_image_descriptions(
    pages: dict[int, list[str]], descriptions_by_page: dict[int, list[str]]
) -> dict[int, list[str]]:
    """
    Dopisuje opisy obrazków (z image_extraction.get_image_descriptions) jako
    dodatkowe linie tekstu na końcu właściwego slajdu, PRZED chunkowaniem —
    dzięki temu opis trafia do tego samego chunku co reszta treści slajdu
    (build_chunks nie wie i nie musi wiedzieć, że część linii pochodzi z GPT,
    a nie z OCR).

    `pages` ma postać {numer_slajdu: [linie_tekstu]} (patrz
    text_cleaning.extract_clean_pages). Jeśli slajd nie miał żadnego tekstu
    z OCR (np. sam obrazek/schemat na całą stronę), a ma opis obrazka,
    tworzymy dla niego wpis w `pages` — inaczej taki slajd w ogóle nie
    trafiłby do build_chunks.
    """
    if not descriptions_by_page:
        return pages

    for page_num, descriptions in descriptions_by_page.items():
        lines = pages.setdefault(page_num, [])
        lines.extend(f"[Opis obrazka]: {d}" for d in descriptions)

    return pages

def _print_debug_images(source_file: str, descriptions_by_page: dict, already_shown: int, limit: int = 10) -> int:
    """Wypisuje opisy obrazków aż do `limit` sztuk łącznie (dla --debug-images)."""
    for page_num, descriptions in sorted(descriptions_by_page.items()):
        for desc in descriptions:
            if already_shown >= limit:
                return already_shown
            print(f"[DEBUG-IMG] {source_file} (slajd {page_num}): {desc}")
            already_shown += 1
    return already_shown

def main(debug_images: bool = False) -> None:
    json_files = sorted(OCR_OUTPUT_DIR.glob("*.json"))
    print(f"Znaleziono {len(json_files)} plików OCR.")

    all_chunks = []
    _debug_shown = 0

    for json_path in json_files:
        source_file = json_path.stem
        meta = get_lesson_meta(source_file)

        result = load_ocr_result(json_path)
        pages = extract_clean_pages(result)

        pdf_path = PDF_INPUT_DIR / f"{source_file}.pdf"
        if pdf_path.exists():
            descriptions_by_page = get_image_descriptions(pdf_path, IMAGES_CACHE_DIR)
            pdf_path = PDF_INPUT_DIR / f"{source_file}.pdf"
            if pdf_path.exists():
                descriptions_by_page = get_image_descriptions(pdf_path, IMAGES_CACHE_DIR)
                if debug_images:
                    _debug_shown = _print_debug_images(source_file, descriptions_by_page, _debug_shown)
                pages = merge_image_descriptions(pages, descriptions_by_page)
            pages = merge_image_descriptions(pages, descriptions_by_page)
        else:
            print(f"[UWAGA] Nie znaleziono pliku PDF ({pdf_path}) — pomijam opisy obrazków dla {source_file}.")

        chunks = build_chunks(
            pages=pages,
            subject=meta["subject"],
            lesson_title=meta["lesson_title"],
            source_file=source_file,
        )

        all_chunks.extend(chunks)
        print(f"[OK] {source_file}: {len(pages)} slajdów -> {len(chunks)} chunków")

    all_chunks.sort(
        key=lambda c: int(re.search(r"\d+", str(c.get("lesson_id", ""))).group())
        if re.search(r"\d+", str(c.get("lesson_id", "")))
        else c.get("lesson_id", "")
    )

    CHUNKS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\nZapisano {len(all_chunks)} chunków do {CHUNKS_OUTPUT_PATH}")
    chunk_sanity_check(all_chunks)


def chunk_sanity_check(chunks: list[dict]) -> None:
    word_counts = sorted(len(c["content"].split()) for c in chunks)
    n = len(word_counts)
    if n == 0:
        return

    print("\n--- Rozkład długości chunków (liczba słów) ---")
    print(f"min: {word_counts[0]}, mediana: {word_counts[n // 2]}, max: {word_counts[-1]}")

    short = [c for c in chunks if len(c["content"].split()) < MIN_WORDS_PER_CHUNK]
    if short:
        print(f"UWAGA: {len(short)} chunków wciąż ma < {MIN_WORDS_PER_CHUNK} słów mimo mergowania — sprawdź ręcznie:")
        for c in short[:5]:
            preview = c["content"][:60].replace("\n", " ")
            print(f"  - {c['chunk_id']}: \"{preview}...\"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug-images",
        action="store_true",
        help="Wypisz opisy pierwszych 10 przetworzonych obrazków (do weryfikacji jakości)",
    )
    args = parser.parse_args()
    main(debug_images=args.debug_images)