"""
text_cleaning.py

Czyszczenie surowego wyniku OCR (Azure Document Intelligence, prebuilt-layout)
zapisanego jako JSON (result.as_dict()) przez process_ocr.py.

Odfiltrowuje nagłówki/stopki/numery stron na podstawie pola "role" i grupuje
pozostały tekst per numer slajdu (strony PDF).
"""

import json
import re
from pathlib import Path

# Role paragrafów, które chcemy odrzucić — to szum, nie treść merytoryczna.
# (dokładnie takie stringi, jakie Azure zwraca w polu "role" w JSON-ie)
SKIP_ROLES = {"pageHeader", "pageFooter", "pageNumber"}

LESSON_MARKER_RE = re.compile(r"^LESSON\s+\d+$", re.IGNORECASE)

# Paragrafy, których górne krawędzie różnią się o mniej niż tyle cali,
# traktujemy jako ten sam "wiersz" przy sortowaniu w kolejności czytania.
ROW_TOLERANCE_INCHES = 0.3

# Przerwa w lewej krawędzi (x_left) większa niż tyle cali oznacza nową kolumnę
# — rozdziela np. wąską kolumnę bloków Ardublock po lewej od akapitów tekstu
# po prawej, które inaczej wplotłyby się w siebie (nakładające się zakresy y).
COLUMN_GAP_INCHES = 1.0


def normalize_line(text: str) -> str:
    """Usuwa wielokrotne spacje/łamania linii, które czasem zostają z OCR."""
    return " ".join(text.split())


def _paragraph_position(paragraph: dict) -> tuple[float, float]:
    """Zwraca (y_top, x_left) lewego górnego rogu paragrafu, w calach."""
    polygon = paragraph["boundingRegions"][0]["polygon"]
    xs = polygon[0::2]
    ys = polygon[1::2]
    return min(ys), min(xs)


def sort_reading_order(
    paragraphs: list[dict],
    row_tolerance: float = ROW_TOLERANCE_INCHES,
    column_gap: float = COLUMN_GAP_INCHES,
) -> list[dict]:
    """
    Sortuje paragrafy w kolejności czytania na podstawie ich pozycji na stronie,
    zamiast polegać na oryginalnej kolejności zwróconej przez Azure.

    Dwuetapowo:
    1. Grupujemy paragrafy w "kolumny" na podstawie przerw w x_left. To
       rozdziela np. wąską kolumnę bloków Ardublock po lewej od szerokich
       akapitów tekstu po prawej — bez tego kroku takie elementy mieszają
       się, bo mają nakładające się zakresy y (samo sortowanie góra->dół
       ich nie rozdzieli).
    2. W obrębie każdej kolumny sortujemy góra->dół (z tolerancją
       `row_tolerance` dla elementów w tym samym wierszu, wtedy dodatkowo
       lewo->prawo).

    Kolumny są łączone od lewej do prawej. Paragrafy z rolą "title" (Azure
    sam je otagował) trafiają zawsze na początek, posortowane po y — bo
    wizualnie bywają wyśrodkowane na banerze slajdu, przez co ich x_left
    potrafi wypaść w innej "kolumnie" niż treść, którą logicznie poprzedzają.
    """
    titles = [p for p in paragraphs if p.get("role") == "title"]
    titles.sort(key=lambda p: _paragraph_position(p)[0])

    rest = [p for p in paragraphs if p.get("role") != "title"]
    positioned = [(p, *_paragraph_position(p)) for p in rest]  # (paragraf, y_top, x_left)

    by_x = sorted(positioned, key=lambda item: item[2])
    columns: list[list[tuple]] = []
    for item in by_x:
        if columns and item[2] - columns[-1][-1][2] <= column_gap:
            columns[-1].append(item)
        else:
            columns.append([item])

    ordered = list(titles)
    for column in columns:
        column.sort(key=lambda item: item[1])  # góra -> dół
        rows: list[list[tuple]] = []
        for item in column:
            if rows and abs(item[1] - rows[-1][0][1]) <= row_tolerance:
                rows[-1].append(item)
            else:
                rows.append([item])
        for row in rows:
            row.sort(key=lambda item: item[2])  # w obrębie wiersza: lewo -> prawo
            ordered.extend(p for p, _, _ in row)

    return ordered


def extract_clean_pages(result: dict) -> dict[int, list[str]]:
    """
    Zwraca {numer_slajdu: [linie_tekstu]} po odfiltrowaniu nagłówków/stopek/
    numeracji i po ustawieniu paragrafów w kolejności czytania (patrz
    `sort_reading_order`).

    `result` to zawartość pliku JSON zapisanego przez process_ocr.py
    (czyli result.as_dict() z Azure SDK) — klucze są w camelCase, np.
    "boundingRegions", "pageNumber", tak jak zwraca je REST API.
    """
    pages_paragraphs: dict[int, list[dict]] = {}
    for paragraph in result.get("paragraphs", []):
        if paragraph.get("role") in SKIP_ROLES:
            continue

        bounding_regions = paragraph.get("boundingRegions")
        if not bounding_regions:
            continue  # paragraf bez przypisania do strony — pomijamy

        page_num = bounding_regions[0]["pageNumber"]
        pages_paragraphs.setdefault(page_num, []).append(paragraph)

    pages: dict[int, list[str]] = {}
    for page_num, paragraphs in pages_paragraphs.items():
        ordered = sort_reading_order(paragraphs)
        lines = [normalize_line(p["content"]) for p in ordered]
        lines = [line for line in lines if line]
        if lines:
            pages[page_num] = lines

    return pages


def extract_tables(result: dict) -> list[dict]:
    """
    Zwraca listę tabel jako osobnych obiektów (nie miesza ich z tekstem paragrafów).
    Każda tabela trafia jako Markdown, z numerem slajdu z pierwszego bounding region.
    Przyda się, jeśli w slajdach pojawią się np. specyfikacje/tabele porównawcze.
    """
    tables_out = []
    for table in result.get("tables", []):
        bounding = table.get("boundingRegions")
        page_num = bounding[0]["pageNumber"] if bounding else None

        row_count = table["rowCount"]
        col_count = table["columnCount"]
        grid = [["" for _ in range(col_count)] for _ in range(row_count)]
        for cell in table["cells"]:
            grid[cell["rowIndex"]][cell["columnIndex"]] = normalize_line(cell["content"])

        header, *body_rows = grid
        md_lines = ["| " + " | ".join(header) + " |", "|" + "---|" * col_count]
        for row in body_rows:
            md_lines.append("| " + " | ".join(row) + " |")

        tables_out.append({
            "page_number": page_num,
            "markdown": "\n".join(md_lines),
        })

    return tables_out


def detect_lesson_title(result: dict) -> str:
    """
    Wyciąga temat lekcji ze strony 1: pierwszy paragraf BEZ roli "title"
    (a więc nie nazwa przedmiotu) i nie pasujący do wzorca "LESSON N".

    Działa, bo szablon slajdu tytułowego jest stały w całej talii:
    1. nazwa przedmiotu (role="title")
    2. temat lekcji (bez roli)          <- to zwracamy
    3. "LESSON N" (bez roli)

    Rzuca ValueError, jeśli nie znajdzie pasującego paragrafu — w takim
    wypadku dopisz wyjątek ręcznie do lessons_manifest.LESSON_OVERRIDES.
    """
    page1_paragraphs = [
        p for p in result.get("paragraphs", [])
        if p.get("boundingRegions") and p["boundingRegions"][0]["pageNumber"] == 1
    ]
    for p in sort_reading_order(page1_paragraphs):
        if p.get("role") == "title":
            continue
        content = p["content"].strip()
        if LESSON_MARKER_RE.match(content):
            continue
        return content

    raise ValueError(
        "Nie udało się automatycznie wykryć tematu lekcji ze strony 1 — "
        "dopisz wpis ręcznie do lessons_manifest.LESSON_OVERRIDES."
    )


def load_ocr_result(json_path: Path) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)