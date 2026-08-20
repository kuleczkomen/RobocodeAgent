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
"Arduino Junior Lesson 17 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Wstęp",
    "lesson_id": "17"
},
"Arduino Junior Lesson 18 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Zmienne i warunki",
    "lesson_id": "18"
},
"Arduino Junior Lesson 19 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Piny analogowe",
    "lesson_id": "19"
},
"Arduino Junior Lesson 20 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Biblioteki w C++",
    "lesson_id": "20"
},
"Arduino Junior Lesson 21-22 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Biblioteki w C++. Część 2",
    "lesson_id": "21-22"
},
"Arduino Junior Lesson 23 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Praca z liczbami losowymi w C++",
    "lesson_id": "23"
},
"Arduino Junior Lesson 24 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Pętle",
    "lesson_id": "24"
},
"Arduino Junior Lesson 25 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Pętle. Część 2",
    "lesson_id": "25"
},
"Arduino Junior Lesson 26 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Funkcje",
    "lesson_id": "26"
},
"Arduino Junior Lesson 27 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Funkcje. Część 2",
    "lesson_id": "27"
},
"Arduino Junior Lesson 28-29 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Czytnik linii papilarnych",
    "lesson_id": "28-29"
},
"Arduino Junior Lesson 30 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Powtórzenie",
    "lesson_id": "30"
},
"Arduino Junior Lesson 32 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "App Inventor. Gra Clicker",
    "lesson_id": "32"
},
"Arduino Junior Lesson 33 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "App Inventor. Akcelerometr",
    "lesson_id": "33"
},
"Arduino Junior Lesson 34 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "App Inventor. Gra Space Shooter",
    "lesson_id": "34"
},
"Arduino Junior Lesson 35-36 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Sterowanie platformą",
    "lesson_id": "35-36"
}
}


def get_lesson_meta(source_file_stem: str) -> dict:
    try:
        return LESSONS[source_file_stem]
    except KeyError as exc:
        raise KeyError(
            f"Brak metadanych dla '{source_file_stem}' w lessons_manifest.py — dodaj wpis."
        ) from exc