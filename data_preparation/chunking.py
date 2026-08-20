"""
chunking.py

Budowa chunków (co do zasady: 1 chunk = 1 slajd, z metadanymi) na podstawie
tekstu przygotowanego przez text_cleaning.py. Bardzo krótkie slajdy są
doklejane do sąsiedniego, żeby nie mieć pustych/bezwartościowych embeddingów.

Dodatkowo: każdy chunk dostaje pole "lesson_id" (np. "L4", "L11-12"),
wyciągane regexem z source_file (typu "Arduino Junior Lesson 11-12 PL").
Dzięki temu retrieve_chunks() w rag_query.py może filtrować po numerze
lekcji (search_kwargs["filter"] = f"lesson_id eq '{lesson_id}'") zamiast
polegać wyłącznie na podobieństwie semantycznym — bo samo embedowanie
tekstu pytania "lekcja 11-12" NIE gwarantuje, że wyszukiwarka nie podciągnie
też sąsiednich lekcji (9, 13 itd.), skoro treściowo są podobne.

WAŻNE: pole "lesson_id" musi być dodane do schematu indeksu Azure AI Search
jako filterable (i zaindeksowane na nowo dla istniejących dokumentów), żeby
filtr eq na nim faktycznie działał.
"""

import re

MIN_WORDS_PER_CHUNK = 20

# Dopasowuje "Lesson 4", "Lesson 11-12", niezależnie od wielkości liter,
# w dowolnym miejscu nazwy pliku/tytułu (np. "Arduino Junior Lesson 11-12 PL").
_LESSON_RE = re.compile(r"Lesson\s+(\d+(?:-\d+)?)", re.IGNORECASE)


def _word_count(text: str) -> int:
    return len(text.split())


def _extract_lesson_id(source_file: str) -> str:
    """'Arduino Junior Lesson 4 PL' -> 'L4'; 'Arduino Junior Lesson 11-12 PL' -> 'L11-12'.

    Jeśli konwencja nazewnictwa plików się zmieni i wzorzec nie złapie
    numeru lekcji, zwracamy None — lepiej mieć wyraźny brak filtra niż
    milcząco błędny lesson_id, który wygląda na poprawny.
    """
    match = _LESSON_RE.search(source_file)
    if not match:
        return None
    return f"L{match.group(1)}"


def build_chunks(
    pages: dict[int, list[str]],
    subject: str,
    lesson_title: str,
    source_file: str,
    min_words: int = MIN_WORDS_PER_CHUNK,
) -> list[dict]:
    """
    Zamienia {numer_slajdu: [linie]} na listę chunków z metadanymi.

    Slajdy krótsze niż `min_words` są doklejane do NASTĘPNEGO slajdu
    (a jeśli to ostatni slajd w lekcji — do poprzedniego), więc jeden
    chunk może w efekcie obejmować kilka numerów slajdów — stąd pole
    "slide_numbers" (lista), a nie pojedynczy "slide_number".
    """
    lesson_id = _extract_lesson_id(source_file)
    if lesson_id is None:
        # Nie blokujemy builda (chunk i tak trafi do indeksu), ale trzeba
        # to zauważyć — bez lesson_id filtrowanie po lekcji nie zadziała
        # dla tego pliku.
        print(
            f"[chunking.py] UWAGA: nie udało się wyciągnąć numeru lekcji z "
            f"source_file={source_file!r} — lesson_id będzie None dla tych chunków."
        )

    ordered_slides = sorted(pages.items())  # [(numer_slajdu, [linie]), ...]

    # 1. sklej linie w treść per slajd, odsiej puste
    slides = [
        (slide_num, "\n".join(lines).strip())
        for slide_num, lines in ordered_slides
        if "\n".join(lines).strip()
    ]

    # 2. dolituj bardzo krótkie slajdy do sąsiada (do następnego w kolejności)
    merged: list[tuple[list[int], str]] = []
    for slide_num, content in slides:
        if merged and _word_count(content) < min_words:
            prev_nums, prev_content = merged[-1]
            merged[-1] = (prev_nums + [slide_num], prev_content + "\n" + content)
        else:
            merged.append(([slide_num], content))

    # jeśli PIERWSZY slajd też wyszedł za krótki, a jest kolejny — dolituj go do następnego
    if len(merged) > 1 and _word_count(merged[0][1]) < min_words:
        first_nums, first_content = merged.pop(0)
        next_nums, next_content = merged[0]
        merged[0] = (first_nums + next_nums, first_content + "\n" + next_content)

    # 3. zbuduj finalne chunki z metadanymi
    chunks = []
    for slide_nums, content in merged:
        chunks.append({
            "chunk_id": f"{source_file}_{slide_nums[0]}",
            "content": content,
            "subject": subject,
            "lesson_title": lesson_title,
            "lesson_id": lesson_id,
            "slide_numbers": slide_nums,
            "source_file": source_file,
        })
    return chunks