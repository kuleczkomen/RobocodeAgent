import os
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

# read from .env
load_dotenv()

ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

if not ENDPOINT or not KEY:
    raise ValueError("Environment variables are missing in .env file.")

# initialise SDK Azure client
client = DocumentIntelligenceClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(KEY)
)

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

input_dir = BASE_DIR / "dataset" / "arduino_junior"
output_dir = BASE_DIR / "output" / "arduino_junior"

pdf_files = list(input_dir.glob("*.pdf"))
print(f"Znaleziono {len(pdf_files)} plików PDF.")

for pdf_path in pdf_files:
    output_json_path = output_dir / f"{pdf_path.stem}.json"

    # cache
    if output_json_path.exists():
        print(f"[CACHE] Pomijam plik (JSON już istnieje): {pdf_path.name}")
        continue
    print(f"[OCR] Wysyłanie do Azure: {pdf_path.name}...")

    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=f,
            content_type="application/octet-stream"
        )
        result = poller.result()

    result_dict = result.as_dict()

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)

    print(f"[SUKCES] Zapisano wynik: {output_json_path}")