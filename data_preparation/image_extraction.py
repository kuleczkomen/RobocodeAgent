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
from openai import OpenAI
import io
from PIL import Image
from utils import config
import argparse
import os
import glob
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytesseract

TEXT_HEAVY_WORD_THRESHOLD = 5

client = OpenAI(
    api_key=config.AI_CHAT_KEY,
    base_url=f"{config.AI_CHAT_ENDPOINT}/openai/v1/"
)
deployment_name = config.AI_CHAT_NAME


def process_image_with_gpt(image_base64: str) -> dict:
    """Wysyła obraz do GPT i decyduje co z nim zrobić."""

    prompt = """
    Jesteś asystentem przetwarzającym zdjęcia z prezentacji edukacyjnej.

    Twoim zadaniem jest sklasyfikować obraz i, jeśli to konieczne, wyciągnąć z niego informacje.

    ZASADY:
    1. Jeśli obraz przedstawia przede wszystkim kota (lub koty), zignoruj go. Służy tylko jako dodatek dla dzieci. Zwróć JSON z polem "action": "ignore" i "reason": "cat".
    2. Jeśli obraz to przede wszystkim zdjęcie z dużą ilością tekstu (np. zdjęcie jakiegoś tekstu, kodu programistycznego, bloczków tekstowych), zignoruj go. Zwróć JSON z polem "action": "ignore" i "reason": "text_heavy".
    3. W każdym innym przypadku (np. schematy, wykresy, inne zdjęcia tematyczne), opisz szczegółowo co znajduje się na obrazku, aby przekazać jego wartość merytoryczną. Zwróć JSON z polem "action": "keep" i polem "description": "tutaj twój szczegółowy opis".

    Zwróć TYLKO czysty obiekt JSON (bez znaczników formatowania Markdown i bloków kodu), zgodnie z powyższymi wytycznymi.
    """

    response = client.responses.create(
        extra_body={
            "agent_reference": {
                "name": "robo-gpt",
                "type": "agent_reference",
            }
        },
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{image_base64}"
                    }
                ]
            }
        ],
        max_output_tokens=500
    )

    try:
        raw_response = response.output_text.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:-3]
        elif raw_response.startswith('```'):
            raw_response = raw_response[3:-3]

        result = json.loads(raw_response)
        return result
    except json.JSONDecodeError:
        return {"action": "error", "reason": "Nie można sparsować odpowiedzi z GPT."}

def extract_and_process_images(pdf_path: str, max_workers: int = 6) -> list[dict]:
    """Otwiera PDF, wyciąga obrazy, odrzuca duplikaty (po hashu zawartości)
    i puszcza unikalne obrazy RÓWNOLEGLE przez GPT — slajdy z powtarzającymi
    się ikonkami (np. rozpiska zajęć) nie odpytują GPT po kilkadziesiąt razy
    dla tego samego obrazka."""

    pdf_document = fitz.open(pdf_path)

    # (numer_strony, numer_obrazu, bytes, hash)
    candidates: list[tuple[int, int, bytes, str]] = []

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

            image_hash = hashlib.md5(image_bytes).hexdigest()
            candidates.append((page_index + 1, img_index + 1, image_bytes, image_hash))

    pdf_document.close()

    unique_by_hash: dict[str, bytes] = {}
    for _, _, image_bytes, image_hash in candidates:
        unique_by_hash.setdefault(image_hash, image_bytes)

    print(
        f"Znaleziono {len(candidates)} obrazów ({len(unique_by_hash)} unikalnych) "
        f"— przetwarzam równolegle ({max_workers} wątków)..."
    )

    results_by_hash: dict[str, dict] = {}
    to_submit: dict[str, bytes] = {}

    for image_hash, image_bytes in unique_by_hash.items():
        to_submit[image_hash] = image_bytes

    print(
        f"Znaleziono {len(candidates)} obrazów ({len(unique_by_hash)} unikalnych, "
        f"{len(unique_by_hash) - len(to_submit)} odfiltrowanych lokalnie jako text_heavy) "
        f"— wysyłam do GPT {len(to_submit)} ({max_workers} wątków)..."
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_hash = {
            executor.submit(
                process_image_with_gpt, base64.b64encode(image_bytes).decode("utf-8")
            ): image_hash
            for image_hash, image_bytes in to_submit.items()
        }
        for future in as_completed(future_to_hash):
            image_hash = future_to_hash[future]
            results_by_hash[image_hash] = future.result()

    extracted_data = []
    seen_on_page: set[tuple[int, str]] = set()
    for page_num, img_index, _, image_hash in candidates:
        gpt_result = results_by_hash[image_hash]

        if gpt_result.get("action") == "keep":
            key = (page_num, image_hash)
            if key in seen_on_page:
                print(f"Strona {page_num}, obraz {img_index} -> pominięto (duplikat na tym slajdzie).")
                continue
            seen_on_page.add(key)

            extracted_data.append({
                "page": page_num,
                "image_index": img_index,
                "description": gpt_result.get("description")
            })
            print(f"Strona {page_num}, obraz {img_index} -> zachowano. Opis: {gpt_result.get('description')[:50]}...")
        elif gpt_result.get("action") == "ignore":
            print(f"Strona {page_num}, obraz {img_index} -> zignorowano. Powód: {gpt_result.get('reason')}")
        else:
            print(f"Strona {page_num}, obraz {img_index} -> błąd przetwarzania: {gpt_result}")

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