from pathlib import Path

def get_output_path(base_path: Path, counter: int = 1) -> Path:
    if not base_path.exists():
        return base_path

    while True:
        new_path = base_path.with_name(f"{base_path.stem}({counter}){base_path.suffix}")

        if not new_path.exists():
            return new_path
        counter += 1