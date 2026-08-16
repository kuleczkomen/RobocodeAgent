import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "embeddings" else Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_EMBEDDING_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_NAME")

def validate_config() -> None:
    """Opcjonalna walidacja – rzuca błąd, jeśli brakuje którejkolwiek zmiennej."""
    missing = [
        name for name, val in [
            ("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT),
            ("AZURE_DOCUMENT_INTELLIGENCE_KEY", AZURE_DOCUMENT_INTELLIGENCE_KEY),
            ("AZURE_SEARCH_ENDPOINT", AZURE_SEARCH_ENDPOINT),
            ("AZURE_SEARCH_KEY", AZURE_SEARCH_KEY),
            ("AZURE_SEARCH_INDEX_NAME", AZURE_SEARCH_INDEX_NAME),
            ("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT),
            ("AZURE_OPENAI_KEY", AZURE_OPENAI_KEY),
            ("AZURE_OPENAI_EMBEDDING_NAME", AZURE_OPENAI_EMBEDDING_NAME),
        ] if not val
    ]
    if missing:
        raise ValueError(f"Brakujące zmienne w .env ({ENV_PATH}): {', '.join(missing)}")