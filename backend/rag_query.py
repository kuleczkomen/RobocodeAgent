"""
rag_query.py — rdzeń Fazy 3: retrieval + generacja.

Zaprojektowany jako moduł (nie skrypt jednorazowy), żeby:
- cli_test.py mógł go używać do ręcznej iteracji promptów,
- eval_runner.py (Faza 4) mógł wywoływać ask() programowo na całym eval_set.json
  bez kopiowania logiki.
"""

from utils import config
from openai import OpenAI, AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
import re

embedding_client = AzureOpenAI(
    azure_endpoint=config.OPENAI_ENDPOINT,
    api_key=config.OPENAI_KEY,
    api_version=config.AZURE_API_VERSION
)

chat_client = OpenAI(
    api_key=config.AI_CHAT_KEY,
    base_url=f"{config.AI_CHAT_ENDPOINT}/openai/v1/"
)

search_client = SearchClient(
    endpoint=config.SEARCH_ENDPOINT,
    index_name=config.SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(config.SEARCH_KEY)
)

EMBEDDING_DEPLOYMENT = config.EMBEDDING_NAME
CHAT_DEPLOYMENT = config.AI_CHAT_NAME

# łapie: "lekcja 4", "lekcji 11-12", "lekcję 3", "L4", "l11-12"
LESSON_QUERY_RE = re.compile(
    r"(?:lekcj\w*\s+|L)(\d+(?:-\d+)?)",
    re.IGNORECASE,
)

def detect_lesson_id(question: str) -> str | None:
    match = LESSON_QUERY_RE.search(question)
    return f"L{match.group(1)}" if match else None

def embed_query_test(text: str) -> list[float]:
    print("Calling embeddings...")
    response = embedding_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text
    )
    return response.data[0].embedding

def embed_query(text: str) -> list[float]:
    response = embedding_client.embeddings.create(model=EMBEDDING_DEPLOYMENT, input=text)
    return response.data[0].embedding


def retrieve_chunks(
        question: str,
        top_k: int = 5,
        subject_filter: str | None = None,
        lesson_filter: str | None = None
):
    """Wyszukiwanie hybrydowe: vector (kNN) + keyword (BM25), łączone przez RRF.
    Dostępne na Free tier — semantic ranker (L2 rerank) NIE jest dostępny na Free,
    wymaga tier Basic+."""
    query_vector = embed_query(question)
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector",
    )

    search_kwargs = dict(
        search_text=question,  # dodanie search_text obok vector_queries = hybrid (RRF)
        vector_queries=[vector_query],
        top=top_k,
        select=["id", "content", "subject", "lesson_title", "lesson_id", "slide_numbers", "source_file"],    )

    filters = []
    if subject_filter:
        filters.append(f"subject eq '{subject_filter}'")
    if lesson_filter:
        filters.append(f"lesson_id eq '{lesson_filter}'")
    if filters:
        search_kwargs["filter"] = " and ".join(filters)

    return list(search_client.search(**search_kwargs))


def build_context(chunks) -> str:
    parts = []
    for c in chunks:
        slides = ",".join(str(s) for s in c["slide_numbers"])
        parts.append(f"[Lekcja: {c['lesson_title']} | Slajdy: {slides}]\n{c['content']}")
    return "\n\n---\n\n".join(parts)


def ask(
        question: str,
        top_k: int = 5,
        subject_filter: str | None = None,
        lesson_filter: str | None = None
) -> dict:

    if lesson_filter is None:
        lesson_filter = detect_lesson_id(question)

    chunks = retrieve_chunks(question, top_k=top_k, subject_filter=subject_filter, lesson_filter=lesson_filter)
    context = build_context(chunks)

    # messages = [
    #     {"role": "system", "content": SYSTEM_PROMPT},
    #     {"role": "user", "content": f"Kontekst:\n{context}\n\nPytanie nauczyciela: {question}"},
    # ]

    response = chat_client.responses.create(
        extra_body={
            "agent_reference": {
                "name": "robo-gpt",
                "type": "agent_reference",
            }
        },
        input=f"Kontekst:\n{context}\n\nPytanie nauczyciela: {question}",
    )

    return {
        "question": question,
        "answer": response.output_text,
        "retrieved_chunks": [
            {
                "id": c["id"],
                "lesson_title": c["lesson_title"],
                "slide_numbers": c["slide_numbers"],
            }
            for c in chunks
        ],
    }
