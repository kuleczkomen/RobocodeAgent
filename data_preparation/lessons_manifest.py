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
    # ARDUINO JUNIOR

    "Arduino Junior Lesson 1 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Wprowadzenie do robotyki",
    },
    "Arduino Junior Lesson 2 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Inteligentna bramka obrotowa",
    },
    "Arduino Junior Lesson 3 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "System bezpieczeństwa",
    },
    "Arduino Junior Lesson 4 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Inteligentna lampa",
    },
    "Arduino Junior Lesson 5 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Joystick",
    },
    "Arduino Junior Lesson 6 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Wskaźnik siedmiosegmentowy",
    },
    "Arduino Junior Lesson 7 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Wyświetlacz i czujnik temperatury",
    },
    "Arduino Junior Lesson 8 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Sterownik silnika i platforma LEO",
    },
"Arduino Junior Lesson 9 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Сzujnik parkowania. Sonar",
    },
"Arduino Junior Lesson 10 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Pasywny głośnik piezo. Pianino",
    },
"Arduino Junior Lesson 11-12 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Pilot zdalnego sterowania",
    },
"Arduino Junior Lesson 13 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Praca z liczbami losowymi",
    },
"Arduino Junior Lesson 14 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Czujnik gazu i przekaźnik",
    },
"Arduino Junior Lesson 16 PL": {
        "subject": "Arduino Junior",
        "lesson_title": "Czujnik gazu i przekaźnik",
},
"Arduino Junior Lesson 17 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Wstęp",
},
"Arduino Junior Lesson 18 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Zmienne i warunki",
},
"Arduino Junior Lesson 19 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Piny analogowe",
},
"Arduino Junior Lesson 20 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Biblioteki w C++",
},
"Arduino Junior Lesson 21-22 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Biblioteki w C++. Część 2",
},
"Arduino Junior Lesson 23 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Praca z liczbami losowymi w C++",
},
"Arduino Junior Lesson 24 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Pętle",
},
"Arduino Junior Lesson 25 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Pętle. Część 2",
},
"Arduino Junior Lesson 26 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Funkcje",
},
"Arduino Junior Lesson 27 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Funkcje. Część 2",
},
"Arduino Junior Lesson 28-29 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Czytnik linii papilarnych",
},
"Arduino Junior Lesson 30 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "C++. Powtórzenie",
},
"Arduino Junior Lesson 32 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "App Inventor. Gra Clicker",
},
"Arduino Junior Lesson 33 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "App Inventor. Akcelerometr",
},
"Arduino Junior Lesson 34 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "App Inventor. Gra Space Shooter",
},
"Arduino Junior Lesson 35-36 PL": {
    "subject": "Arduino Junior",
    "lesson_title": "Sterowanie platformą",
},


# MIDDLE EMBEDDED
"Middle Embedded Lesson 1 PL": {
    "subject": "Middle Embedded",
    "lesson_title": "Arduino. Powtórzenie",
},
"Middle Embedded Lesson 2 PL": {
    "subject": "Middle Embedded",
    "lesson_title": "Arduino. Powtórzenie",
},
"Middle Embedded Lesson 3 PL": {
    "subject": "Middle Embedded",
    "lesson_title": "Arduino. Powtarzamy C++",
},
"Middle Embedded Lesson 4 PL": {
    "subject": "Middle Embedded",
    "lesson_title": "Arduino. Biblioteki",
},
"Middle Embedded Lesson 5 PL": {
    "subject": "Middle Embedded",
    "lesson_title": "Tinkercad 3D. Wprowadzenie",
},
"Middle Embedded Lesson 6 PL": {
    "subject": "Middle Embedded",
    "lesson_title": "Tinkercad 3D. Ćwiczenia",
},
"Middle Embedded Lesson 7 PL": {
    "subject": "Middle Embedded",
    "lesson_title": "Tinkercad 3D. Biblioteka elementów",
},

}


def get_lesson_meta(source_file_stem: str) -> dict:
    try:
        return LESSONS[source_file_stem]
    except KeyError as exc:
        raise KeyError(
            f"Brak metadanych dla '{source_file_stem}' w lessons_manifest.py — dodaj wpis."
        ) from exc