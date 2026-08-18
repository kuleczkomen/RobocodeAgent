"""
cli_test.py — pętla do ręcznego testowania: zadajesz pytanie, widzisz odpowiedź
i to, jakie fragmenty zostały pobrane. Każda interakcja jest logowana do JSONL —
ten log jest też surowym materiałem do zbudowania eval_set.json w Fazie 4.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from rag_query import ask
from utils import config

LOG_FILE = Path("logs/queries.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)

def test() -> None:
    print("EMBEDDING ENDPOINT:", config.OPENAI_ENDPOINT)
    print("CHAT ENDPOINT:", config.AI_CHAT_ENDPOINT)
    print("API VERSION:", config.AZURE_API_VERSION)


def log_interaction(result: dict) -> None:
    entry = {**result, "timestamp": datetime.now(timezone.utc).isoformat()}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    test()
    print("Zadaj pytanie testowe (Ctrl+C aby wyjść)\n")
    while True:
        try:
            question = input("> ")
        except KeyboardInterrupt:
            break
        if not question.strip():
            continue

        result = ask(question)

        print("\n--- ODPOWIEDŹ ---")
        print(result["answer"])
        print("\n--- POBRANE FRAGMENTY ---")
        for c in result["retrieved_chunks"]:
            print(f"  {c['lesson_title']} — slajdy {c['slide_numbers']}")
        print()

        log_interaction(result)
