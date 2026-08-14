"""
lessons_manifest.py

Metadane per plik lekcji. Nie da się tego w 100% niezawodnie wyciągnąć
z samego OCR — np. w Lesson 1 tytuł przedmiotu ("ROBOCODE ARDUINO JUNIOR")
ma role="title", ale sam temat lekcji ("Wprowadzenie do robotyki") już nie
ma żadnej roli w wyniku Azure, więc nie da się tego odróżnić automatycznie
od zwykłego akapitu. Prościej i pewniej wpisać to ręcznie, raz dla każdej
z 15 lekcji.

Klucz: source_file = stem pliku PDF/JSON (nazwa bez rozszerzenia).
"""

LESSONS = {
    "Arduino Junior Lesson 1 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Wprowadzenie do robotyki",
    },
    # dodaj tu kolejne 14 lekcji, ten sam wzorzec, np.:
    # "Arduino_Junior_Lesson_2_PL": {
    #     "subject": "Arduino Junior",
    #     "lesson_title": "...",
    # },
}


def get_lesson_meta(source_file_stem: str) -> dict:
    try:
        return LESSONS[source_file_stem]
    except KeyError as exc:
        raise KeyError(
            f"Brak metadanych dla '{source_file_stem}' w lessons_manifest.py — dodaj wpis."
        ) from exc