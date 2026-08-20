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
        "lesson_id": "1"
    },
    "Arduino Junior Lesson 2 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Inteligentna bramka obrotowa",
        "lesson_id": "2"
    },
    "Arduino Junior Lesson 3 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "System bezpieczeństwa",
        "lesson_id": "3"
    },
    "Arduino Junior Lesson 4 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Inteligentna lampa",
        "lesson_id": "4"
    },
    "Arduino Junior Lesson 5 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Joystick",
        "lesson_id": "5"
    },
    "Arduino Junior Lesson 6 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Wskaźnik siedmiosegmentowy",
        "lesson_id": "6"
    },
    "Arduino Junior Lesson 7 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Wyświetlacz i czujnik temperatury",
        "lesson_id": "7"
    },
    "Arduino Junior Lesson 8 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Sterownik silnika i platforma LEO",
        "lesson_id": "8"
    },
"Arduino Junior Lesson 9 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Сzujnik parkowania. Sonar",
        "lesson_id": "9"
    },
"Arduino Junior Lesson 10 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Pasywny głośnik piezo. Pianino",
        "lesson_id": "10"
    },
"Arduino Junior Lesson 11-12 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Pilot zdalnego sterowania",
        "lesson_id": "11-12"
    },
"Arduino Junior Lesson 13 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Praca z liczbami losowymi",
        "lesson_id": "13"
    },
"Arduino Junior Lesson 14 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Czujnik gazu i przekaźnik",
        "lesson_id": "14"
    },
"Arduino Junior Lesson 16 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Czujnik gazu i przekaźnik",
        "lesson_id": "16"
    },
}


def get_lesson_meta(source_file_stem: str) -> dict:
    try:
        return LESSONS[source_file_stem]
    except KeyError as exc:
        raise KeyError(
            f"Brak metadanych dla '{source_file_stem}' w lessons_manifest.py — dodaj wpis."
        ) from exc