"""
eval_retrieval.py — automatyczna ewaluacja jakości retrievalu (Faza 4).
"""

import argparse
import json
from pathlib import Path

from backend.rag_query import retrieve_chunks


def load_eval_set(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for i, item in enumerate(data):
        if "question" not in item or "relevant_slides" not in item:
            raise ValueError(
                f"Wpis {i + 1} w {path} musi mieć pola 'question' i 'relevant_slides'. "
                f"Otrzymano: {item}"
            )
        if not item["relevant_slides"]:
            raise ValueError(
                f"Wpis {i + 1} w {path} ma pustą listę 'relevant_slides'."
            )
    return data


def _parse_relevant_slide(slide_str: str) -> tuple[str, int]:
    """'1.2' -> ('1', 2); '11-12.4' -> ('11-12', 4).
    """
    source_file, slide_num = slide_str.split(".", 1)
    return source_file, int(slide_num)


import re


def _normalize_source_file(source_file: str) -> str:
    """Ujednolica source_file do formatu używanego w relevant_slides ('1', '2', '11-12').
    Jeśli konwencja nazewnictwa się zmieni, dostosuj wzorzec `_LESSON_RE`.
    """
    match = _LESSON_RE.search(source_file)
    if match:
        return match.group(1)
    # Nie znaleziono wzorca "Lesson <numer>" — zwróć oryginał (i tak nie
    # dopasuje się do relevant_slides, ale przynajmniej nie wywali błędu;
    # zobaczysz to w --debug i będzie wiadomo, że trzeba poprawić regex).
    return source_file


_LESSON_RE = re.compile(r"Lesson\s+(\d+(?:-\d+)?)", re.IGNORECASE)


def _chunk_slide_numbers(chunk: dict) -> tuple[str, list[int]]:
    """Wyciąga (source_file, slide_numbers) ze zwróconego chunku.

    Dostosuj tę funkcję, jeśli rag_query.py zwraca inne nazwy pól niż te
    ustawiane w chunking.py.
    """
    try:
        return _normalize_source_file(chunk["source_file"]), chunk["slide_numbers"]
    except KeyError as e:
        raise KeyError(
            "Zwrócony chunk nie ma pola "
            f"{e}. retrieve_chunks() (rag_query.py) musi zwracać "
            "'source_file' i 'slide_numbers' w select=[...] — patrz "
            "docstring tego modułu."
        ) from e


def _chunk_hits_targets(chunk: dict, target_slides: set[tuple[str, int]]) -> bool:
    source_file, slide_numbers = _chunk_slide_numbers(chunk)
    return any(
        (source_file, slide_num) in target_slides for slide_num in slide_numbers
    )


def evaluate_retrieval(
        eval_set: list[dict],
        top_k: int = 5,
        subject_filter: str | None = None,
        debug: bool = False,
) -> dict:
    """Liczy Recall@k i MRR dla całego eval_set, plus szczegóły per pytanie —
    przydatne do zobaczenia, które konkretnie pytania nie trafiają w dobry chunk.

    Trafienie = którykolwiek zwrócony chunk pokrywa którykolwiek slajd z
    "relevant_slides" danego pytania (pytania mogą mieć więcej niż jeden
    poprawny slajd/chunk).
    """
    per_question = []
    hits = 0
    reciprocal_ranks = []

    for item in eval_set:
        question = item["question"]
        target_slides = {_parse_relevant_slide(s) for s in item["relevant_slides"]}

        retrieved = retrieve_chunks(question, top_k=top_k, subject_filter=subject_filter)
        retrieved_chunk_ids = [c.get("chunk_id", c.get("id")) for c in retrieved]

        if debug:
            print(f"\n[DEBUG] Pytanie: {question}")
            print(f"[DEBUG]   oczekiwane (target_slides): {sorted(f'{sf}.{sn}' for sf, sn in target_slides)}")
            for i, c in enumerate(retrieved):
                raw_source_file = c.get("source_file")
                norm_source_file = _normalize_source_file(raw_source_file) if raw_source_file else None
                print(
                    f"[DEBUG]   #{i + 1} source_file zwrócony przez index = {raw_source_file!r} "
                    f"(po normalizacji: {norm_source_file!r}), slide_numbers = {c.get('slide_numbers')}"
                )

        rank = None
        for i, chunk in enumerate(retrieved):
            if _chunk_hits_targets(chunk, target_slides):
                rank = i + 1
                break

        if rank is not None:
            hits += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0.0)

        per_question.append({
            "question": question,
            "target_slides": sorted(f"{sf}.{sn}" for sf, sn in target_slides),
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "hit": rank is not None,
            "rank": rank,
        })

    n = len(eval_set)
    recall_at_k = hits / n if n else 0.0
    mrr = sum(reciprocal_ranks) / n if n else 0.0

    return {
        "k": top_k,
        "n_questions": n,
        "recall@k": round(recall_at_k, 4),
        "mrr": round(mrr, 4),
        "per_question": per_question,
    }


def print_summary(results: dict) -> None:
    print(f"\n--- Wyniki retrievalu (k={results['k']}, n={results['n_questions']}) ---")
    print(f"Recall@{results['k']}: {results['recall@k']:.2%}")
    print(f"MRR:        {results['mrr']:.4f}")

    misses = [q for q in results["per_question"] if not q["hit"]]
    if misses:
        print(f"\nPytania bez trafienia w top-{results['k']} ({len(misses)}):")
        for m in misses:
            print(f"  - {m['question']}  (oczekiwane slajdy: {', '.join(m['target_slides'])})")


def main():
    parser = argparse.ArgumentParser(description="Ewaluacja retrievalu RAG (Recall@k, MRR)")
    # Ścieżka do pliku z pytaniami (format: question + relevant_slides)
    parser.add_argument("--eval-set", default="questions.json")
    # top_k dla retrievalu
    parser.add_argument("--k", type=int, default=5)
    # Opcjonalny filtr subject
    parser.add_argument("--subject", default=None)
    # Ścieżka do zapisu pełnych wyników JSON
    parser.add_argument("--output", default=None)
    # Wypisz surowe source_file/slide_numbers dla każdego zwróconego chunku —
    # przydatne do zdiagnozowania niezgodności formatu z relevant_slides
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    eval_set = load_eval_set(args.eval_set)
    results = evaluate_retrieval(eval_set, top_k=args.k, subject_filter=args.subject, debug=args.debug)
    print_summary(results)

    if args.output:
        Path(args.output).write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nPełne wyniki zapisane do {args.output}")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# Jak rozbudować questions.json syntetycznie (poza pytaniami ręcznymi):
#
# Dla każdego chunka w indeksie (masz jego "content", "source_file" i
# "slide_numbers") poproś LLM o 1-2 pytania, na które da się odpowiedzieć
# wyłącznie z tego fragmentu:
#
#   prompt = (
#       "Na podstawie tego fragmentu wygeneruj jedno pytanie, na które "
#       f"da się odpowiedzieć wyłącznie na jego podstawie:\n\n{chunk['content']}"
#   )
#
# Zapisz wynik jako:
#   {
#     "question": <wygenerowane pytanie>,
#     "relevant_slides": [f"{chunk['source_file']}.{n}" for n in chunk['slide_numbers']]
#   }
# do osobnego pliku (np. questions_synthetic.json). Trzymaj go oddzielnie od
# pytań ręcznych (questions.json) i uruchamiaj oba — syntetyczny zbiór do
# regresji przy każdej zmianie, ręczny jako mały "prawdziwy" sanity check.
# ---------------------------------------------------------------------------

