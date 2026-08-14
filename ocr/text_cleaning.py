"""
text_cleaning.py

Czyszczenie surowego wyniku OCR (Azure Document Intelligence, prebuilt-layout)
zapisanego jako JSON (result.as_dict()) przez process_ocr.py.

Odfiltrowuje nagłówki/stopki/numery stron na podstawie pola "role" i grupuje
pozostały tekst per numer slajdu (strony PDF).
"""

import json
from pathlib import Path

# Role paragrafów, które chcemy odrzucić — to szum, nie treść merytoryczna.
# (dokładnie takie stringi, jakie Azure zwraca w polu "role" w JSON-ie)
SKIP_ROLES = {"pageHeader", "pageFooter", "pageNumber"}


def normalize_line(text: str) -> str:
    """Usuwa wielokrotne spacje/łamania linii, które czasem zostają z OCR."""
    return " ".join(text.split())


def extract_clean_pages(result: dict) -> dict[int, list[str]]:
    """
    Zwraca {numer_slajdu: [linie_tekstu]} po odfiltrowaniu nagłówków/stopek/numeracji.

    `result` to zawartość pliku JSON zapisanego przez process_ocr.py
    (czyli result.as_dict() z Azure SDK) — klucze są w camelCase, np.
    "boundingRegions", "pageNumber", tak jak zwraca je REST API.
    """
    pages: dict[int, list[str]] = {}
    for paragraph in result.get("paragraphs", []):
        if paragraph.get("role") in SKIP_ROLES:
            continue

        bounding_regions = paragraph.get("boundingRegions")
        if not bounding_regions:
            continue  # paragraf bez przypisania do strony — pomijamy

        page_num = bounding_regions[0]["pageNumber"]
        line = normalize_line(paragraph["content"])
        if line:
            pages.setdefault(page_num, []).append(line)

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


def load_ocr_result(json_path: Path) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)