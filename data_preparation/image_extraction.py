"""
Ten moduł udostępnia też funkcję get_image_descriptions(), używaną przez
build_dataset.py do automatycznego dociągania opisów obrazków do chunków.

Cache: wynik dla każdego PDF-a jest zapisywany jako JSON w cache_dir
(<nazwa_pdf>.json). Jeśli taki plik już istnieje, GPT NIE jest odpytywane
ponownie — dane wczytywane są z dysku. Działa to analogicznie do cache'u
z process_ocr.py (tam cache = plik output/<subject>/<pdf>.json).
"""

import pymupdf as fitz
import base64
import json
from pathlib import Path
from openai import AzureOpenAI
import io
from PIL import Image
from utils import config
import argparse
import os
import glob

client = AzureOpenAI(
    azure_endpoint=config.OPENAI_ENDPOINT,
    api_key=config.OPENAI_KEY,
    api_version="2024-06-01",
)
deployment_name = config.AI_CHAT_NAME


def process_image_with_gpt(image_base64: str) -> dict:
    """Wysyła obraz do GPT i decyduje co z nim zrobić."""

    prompt = """
    Jesteś asystentem przetwarzającym zdjęcia z prezentacji edukacyjnej.

    Twoim zadaniem jest sklasyfikować obraz i, jeśli to konieczne, wyciągnąć z niego informacje.

    ZASADY:
    1. Jeśli obraz przedstawia przede wszystkim kota (lub koty), zignoruj go. Służy tylko jako przerywnik. Zwróć JSON z polem "action": "ignore" i "reason": "cat".
    2. Jeśli obraz to przede wszystkim zdjęcie z dużą ilością tekstu (np. zdjęcie jakiegoś tekstu, kodu programistycznego, bloczków tekstowych), zignoruj go. Zwróć JSON z polem "action": "ignore" i "reason": "text_heavy".
    3. W każdym innym przypadku (np. schematy, wykresy, inne zdjęcia tematyczne), opisz szczegółowo co znajduje się na obrazku, aby przekazać jego wartość merytoryczną. Zwróć JSON z polem "action": "keep" i polem "description": "tutaj twój szczegółowy opis".

    Zwróć TYLKO czysty obiekt JSON (bez znaczników formatowania Markdown i bloków kodu), zgodnie z powyższymi wytycznymi.
    """

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )

    try:
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:-3]
        elif raw_response.startswith('```'):
            raw_response = raw_response[3:-3]

        result = json.loads(raw_response)
        return result
    except json.JSONDecodeError:
        return {"action": "error", "reason": "Nie można sparsować odpowiedzi z GPT."}


def extract_and_process_images(pdf_path: str) -> list[dict]:
    """Otwiera PDF, wyciąga zdjęcia i puszcza je przez GPT."""

    pdf_document = fitz.open(pdf_path)
    extracted_data = []

    for page_index in range(len(pdf_document)):
        page = pdf_document.load_page(page_index)
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]

            try:
                img_obj = Image.open(io.BytesIO(image_bytes))
                if img_obj.width < 100 or img_obj.height < 100:
                    continue
            except Exception:
                pass

            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            print(f"Przetwarzam obraz {img_index + 1} na stronie {page_index + 1}...")

            gpt_result = process_image_with_gpt(image_base64)

            if gpt_result.get("action") == "keep":
                extracted_data.append({
                    "page": page_index + 1,
                    "image_index": img_index + 1,
                    "description": gpt_result.get("description")
                })
                print(f" -> Zachowano. Opis: {gpt_result.get('description')[:50]}...")
            elif gpt_result.get("action") == "ignore":
                print(f" -> Zignorowano. Powód: {gpt_result.get('reason')}")
            else:
                print(f" -> Błąd przetwarzania: {gpt_result}")

    pdf_document.close()
    return extracted_data


def get_image_descriptions(pdf_path, cache_dir) -> dict:
    """
    Zwraca słownik {numer_strony: [opis1, opis2, ...]} z opisami obrazków
    wyłuskanymi z danego PDF-a (numeracja stron od 1, tak jak w process_ocr /
    Document Intelligence).

    Cache: wynik dla każdego PDF-a jest zapisywany jako
    <cache_dir>/<nazwa_pdf_bez_rozszerzenia>.json. Jeśli plik już istnieje,
    funkcja wczytuje go z dysku zamiast ponownie odpytywać GPT — dzięki temu
    ponowne uruchomienie build_dataset.py nie przetwarza od nowa obrazków
    z już obrobionych slajdów.
    """
    pdf_path = Path(pdf_path)
    cache_dir = Path(cache_dir)
    cache_path = cache_dir / f"{pdf_path.stem}.json"

    if cache_path.exists():
        print(f"[CACHE] Pomijam ekstrakcję obrazów (JSON już istnieje): {pdf_path.name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            extracted_data = json.load(f)
    else:
        print(f"[IMG] Ekstrakcja obrazów z: {pdf_path.name}...")
        extracted_data = extract_and_process_images(str(pdf_path))
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        print(f"[SUKCES] Zapisano opisy obrazów: {cache_path}")

    descriptions_by_page: dict = {}
    for item in extracted_data:
        descriptions_by_page.setdefault(item["page"], []).append(item["description"])

    return descriptions_by_page


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ekstrakcja i analiza obrazów z plików PDF.")
    parser.add_argument("--folder", required=True, help="Ścieżka do folderu z plikami PDF")
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Folder na cache JSON z opisami obrazków (domyślnie: <folder>/_image_cache)",
    )
    args = parser.parse_args()

    folder_path = args.folder

    if not os.path.isdir(folder_path):
        print(f"Błąd: Ścieżka '{folder_path}' nie istnieje lub nie jest folderem.")
        exit(1)

    cache_dir = Path(args.cache_dir) if args.cache_dir else Path(folder_path) / "_image_cache"

    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))

    if not pdf_files:
        print(f"Nie znaleziono plików PDF w folderze: {folder_path}")
        exit(0)

    for pdf_file_path in pdf_files:
        print(f"\n=======================================================")
        print(f"Rozpoczynam analizę pliku: {os.path.basename(pdf_file_path)}")
        print(f"=======================================================")

        descriptions_by_page = get_image_descriptions(pdf_file_path, cache_dir)

        print(f"\n--- WYNIK KOŃCOWY: {os.path.basename(pdf_file_path)} ---")
        for page_num, descs in sorted(descriptions_by_page.items()):
            print(f"Strona {page_num}:")
            for d in descs:
                print(f"  - {d}")
            print("-" * 20)