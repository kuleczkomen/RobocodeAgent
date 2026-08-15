## Na czym polega "indeksowanie embeddingów"

To dwa oddzielne kroki, które łatwo pomylić:

1. **Generowanie embeddingu** — zamiana tekstu chunku na wektor liczb (np. 1536 liczb zmiennoprzecinkowych dla `text-embedding-3-small`), który reprezentuje znaczenie tego tekstu. Robi to model embeddingowy (Azure OpenAI), jeden request = jeden wektor.

2. **Indeksowanie** — wgranie tego wektora (razem z oryginalnym tekstem i metadanymi) do Azure AI Search, które buduje nad wszystkimi wektorami strukturę do szybkiego przeszukiwania przybliżonego najbliższego sąsiedztwa (**HNSW** — Hierarchical Navigable Small World). Bez tej struktury, żeby znaleźć najbliższe chunki dla zapytania, trzeba by porównać wektor zapytania z *każdym* wektorem w bazie (brute force) — przy setkach chunków to jeszcze OK, ale nie skaluje się. HNSW pozwala znaleźć top-k najbliższych wektorów bez przeszukiwania wszystkiego.

Czyli: **embedding to reprezentacja jednego chunku**, **indeksowanie to zorganizowanie wielu takich reprezentacji tak, żeby dało się je szybko przeszukiwać**. W praktyce robisz to w dwóch skryptach — raz tworzysz schemat indeksu, potem (za każdym razem, gdy masz nowe chunki) generujesz embeddingi i je wgrywasz.Składnia obu plików jest poprawna (błąd `ModuleNotFoundError: No module named 'azure'` to tylko brak paczek w tym sandboxie — nie mam dostępu do prawdziwych endpointów Azure z tego środowiska, więc nie przetestuję realnego wywołania, ale logika sanityzacji `id` działa poprawnie, np. spacje z Twojego przykładu `"Arduino Junior Lesson 10 PL_1"` zamieniają się na `_`).Dwa nowe pliki, obok już istniejących w `scripts/`:

- **`create_index.py`** — uruchamiasz raz, tworzy schemat indeksu w Azure AI Search (pola `content`, `content_vector`, metadane).
- **`index_chunks.py`** — czyta `chunks.jsonl`, generuje embeddingi paczkami po 16 (Azure OpenAI), wgrywa do indeksu. Bezpiecznie uruchamiać wielokrotnie po zmianach w chunkach.

Musisz doinstalować pakiety (nie ma ich jeszcze w Twoim projekcie): `pip install azure-search-documents openai python-dotenv`, oraz dopisać do `.env`:
```
AZURE_SEARCH_ENDPOINT=https://<twoja-nazwa>.search.windows.net
AZURE_SEARCH_KEY=...
AZURE_SEARCH_INDEX_NAME=lekcje-arduino
AZURE_OPENAI_ENDPOINT=https://<twoj-resource>.openai.azure.com
AZURE_OPENAI_KEY=...
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

Kolejność uruchomienia: `create_index.py` raz, potem `index_chunks.py` za każdym razem, gdy `build_dataset.py` wygeneruje nowy `chunks.jsonl`.

Jedna rzecz, na którą zwróć uwagę przy pierwszym uruchomieniu: `EMBEDDING_DEPLOYMENT` musi wskazywać na **deployment**, nie na nazwę modelu — w Azure OpenAI tworzysz nazwany deployment (np. nazwałeś go `text-embedding-3-small` albo inaczej) i to ta nazwa idzie do `.env`, nie surowa nazwa modelu z dokumentacji OpenAI.