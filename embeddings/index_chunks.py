"""
index_chunks.py

Faza 3, krok 1: generuje embeddingi dla chunks.jsonl (Azure OpenAI) i
wgrywa je razem z tekstem + metadanymi do indeksu Azure AI Search
utworzonego przez create_index.py.

Uruchom create_index.py raz wcześniej. Ten skrypt można uruchamiać
wielokrotnie — upload_documents nadpisuje dokumenty o tym samym "id",
więc ponowne uruchomienie po zmianach w chunks.jsonl jest bezpieczne.

Uruchomienie:
    python index_chunks.py
"""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI

load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
SUBJECT_NAME = "arduino_junior"
CHUNKS_PATH = BASE_DIR / "output" / f"{SUBJECT_NAME}_chunks.jsonl"

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "lekcje-arduino")

OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

BATCH_SIZE = 16  # ile chunków na jedno wywołanie API embeddingów / upload do indeksu

# Klucz dokumentu w Azure AI Search może zawierać tylko litery, cyfry, podkreślenie, myślnik i znak równości.
# chunk_id bywa ze spacjami/kropkami (zależnie od tego, jak nazwane są pliki źródłowe) — więc czyścimy.
UNSAFE_ID_CHARS_RE = re.compile(r"[^A-Za-z0-9_\-=]")


def safe_id(chunk_id: str) -> str:
    return UNSAFE_ID_CHARS_RE.sub("_", chunk_id)


def load_chunks() -> list[dict]:
    chunks = []
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def batched(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> None:
    for name, value in [
        ("AZURE_SEARCH_ENDPOINT", SEARCH_ENDPOINT),
        ("AZURE_SEARCH_KEY", SEARCH_KEY),
        ("AZURE_OPENAI_ENDPOINT", OPENAI_ENDPOINT),
        ("AZURE_OPENAI_KEY", OPENAI_KEY),
    ]:
        if not value:
            raise ValueError(f"Brak {name} w .env.")

    chunks = load_chunks()
    print(f"Wczytano {len(chunks)} chunków z {CHUNKS_PATH}.")

    openai_client = AzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        api_key=OPENAI_KEY,
        api_version="2024-06-01",
    )
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY),
    )

    uploaded = 0
    for batch in batched(chunks, BATCH_SIZE):
        texts = [c["content"] for c in batch]

        # jeden request embeddingowy na całą paczkę, nie per chunk —
        # dużo szybciej i taniej niż wywołanie API dla każdego chunku osobno
        response = openai_client.embeddings.create(
            model=EMBEDDING_DEPLOYMENT,
            input=texts,
        )
        embeddings = [item.embedding for item in response.data]

        documents = []
        for chunk, vector in zip(batch, embeddings):
            documents.append({
                "id": safe_id(chunk["chunk_id"]),
                "content": chunk["content"],
                "content_vector": vector,
                "subject": chunk["subject"],
                "lesson_title": chunk["lesson_title"],
                "slide_numbers": chunk["slide_numbers"],
                "source_file": chunk["source_file"],
            })

        result = search_client.upload_documents(documents=documents)
        failed = [r for r in result if not r.succeeded]
        if failed:
            print(f"UWAGA: {len(failed)} dokumentów nie wgrało się w tej paczce:")
            for f_ in failed:
                print(f"  - {f_.key}: {f_.error_message}")

        uploaded += len(documents) - len(failed)
        print(f"[OK] Zaindeksowano {uploaded}/{len(chunks)} chunków...")

    print(f"\nGotowe. Zaindeksowano {uploaded}/{len(chunks)} chunków w '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()
