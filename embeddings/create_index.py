"""
create_index.py

Jednorazowy setup: tworzy (lub nadpisuje schemat) indeksu wektorowego
w Azure AI Search pod chunki lekcji. Uruchom raz przed pierwszym
index_chunks.py — a ponownie tylko jeśli zmieniasz schemat pól.

Uruchomienie:
    python create_index.py
"""

import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)

def read_dotenv() -> tuple[str, str, str]:
    load_dotenv()

    ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    KEY = os.getenv("AZURE_SEARCH_KEY")
    INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "lekcje-arduino")

    if not ENDPOINT or not KEY:
        raise ValueError("Brak AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_KEY w .env.")

    return ENDPOINT, KEY, INDEX_NAME

# text-embedding-3-small zwraca wektory o 1536 wymiarach. Jeśli zmienisz
# model embeddingowy na inny (np. -large), zaktualizuj to i przebuduj
# indeks od zera — nie da się zmienić wymiaru istniejącego pola wektorowego.
EMBEDDING_DIMENSIONS = 1536


def main() -> None:
    ENDPOINT, KEY, INDEX_NAME = read_dotenv()
    client = SearchIndexClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))

    index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            # klucz dokumentu — musi być unikalny; patrz safe_id() w index_chunks.py
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            # pełny tekst chunku — przeszukiwalny też klasycznie (keyword search),
            # przydatne do hybrid search później
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=EMBEDDING_DIMENSIONS,
                vector_search_profile_name="default-profile",
            ),
            # metadane — filterable/facetable, żeby dało się np. zawęzić wyszukiwanie do jednej lekcji
            SimpleField(name="subject", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="lesson_title", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(
                name="slide_numbers",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Int32),
                filterable=True,
            ),
            SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True, facetable=True),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
            profiles=[
                VectorSearchProfile(
                    name="default-profile",
                    algorithm_configuration_name="default-hnsw",
                )
            ],
        ),
    )

    client.create_or_update_index(index)
    print(f"Indeks '{INDEX_NAME}' gotowy ({EMBEDDING_DIMENSIONS} wymiarów wektora).")


if __name__ == "__main__":
    main()
