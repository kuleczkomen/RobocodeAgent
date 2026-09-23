import fitz  # PyMuPDF
import base64
import json
from openai import AzureOpenAI
import io
from PIL import Image
from utils import config

client = AzureOpenAI(
    azure_endpoint=config.OPENAI_ENDPOINT,
    api_key=config.OPENAI_KEY,
    api_version=config.AZURE_API_VERSION
)
deployment_name = config.AI_CHAT_NAME


def process_image_with_gpt(image_base64: str) -> dict:
    """Wysyła obraz do GPT-4o mini i decyduje co z nim zrobić."""

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
        # GPT-4o-mini powinien zwrócić czysty JSON, ale dla bezpieczeństwa można oczyścić wynik
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:-3]
        elif raw_response.startswith('```'):
            raw_response = raw_response[3:-3]

        result = json.loads(raw_response)
        return result
    except json.JSONDecodeError:
        return {"action": "error", "reason": "Nie można sparsować odpowiedzi z GPT."}


def extract_and_process_images(pdf_path: str):
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
            image_ext = base_image["ext"]

            # PyMuPDF czasami wyciąga bardzo małe ikony lub elementy tła
            # Pomijamy obrazy mniejsze niż np. 100x100 pikseli (możesz dostosować)
            try:
                img_obj = Image.open(io.BytesIO(image_bytes))
                if img_obj.width < 100 or img_obj.height < 100:
                    continue
            except Exception:
                pass  # Jeśli z jakiegoś powodu PIL nie może otworzyć z pamięci, próbujemy procesować dalej

            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            print(f"Przetwarzam obraz {img_index + 1} na stronie {page_index + 1}...")

            # Wysłanie do GPT
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

    return extracted_data


# Użycie
if __name__ == "__main__":
    pdf_file_path = "twoja_prezentacja.pdf"  # Podmień na ścieżkę do Twojego pliku
    results = extract_and_process_images(pdf_file_path)

    print("\n\n--- WYNIK KOŃCOWY ---")
    for res in results:
        print(f"Strona {res['page']}, Obraz {res['image_index']}:")
        print(res['description'])
        print("-" * 20)