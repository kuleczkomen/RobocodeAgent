from pathlib import Path
import argparse
import subprocess
import sys


def find_pptx_files(input_folder: Path) -> list[Path]:
    """Find PPTX files anywhere under input_folder, grouped by parent folder;
    if a parent folder has multiple .pptx files, keep only the one ending in PL.pptx."""
    by_parent: dict[Path, list[Path]] = {}
    for f in input_folder.rglob("*.pptx"):
        by_parent.setdefault(f.parent, []).append(f)

    files = []
    for parent, sub_files in by_parent.items():
        if len(sub_files) > 1:
            pl_files = [f for f in sub_files if f.name.endswith("PL.pptx")]
            sub_files = pl_files if pl_files else sub_files
        files.extend(sub_files)

    return files


def convert_pptx_to_pdf(subject_name: str, input_folder: Path) -> None:
    output_folder = Path(f"../dataset/{subject_name}")

    if not input_folder.exists():
        print(f"Input folder does not exist: {input_folder}")
        sys.exit(1)

    output_folder.mkdir(parents=True, exist_ok=True)

    pptx_files = find_pptx_files(input_folder)

    if not pptx_files:
        print(f"No .pptx files found in: {input_folder}")
        return

    print(f"Found {len(pptx_files)} PPTX files.")

    for pptx_file in pptx_files:
        print(f"Converting: {pptx_file}")

        try:
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(output_folder),
                    str(pptx_file),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            print(f"  -> {pptx_file.stem}.pdf")

        except subprocess.CalledProcessError as e:
            print(f"ERROR converting {pptx_file.name}")
            print(e.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Convert all PPTX files from input folder to PDF."
    )
    parser.add_argument("--subject-name")
    parser.add_argument("--input", help="Input folder with PDF presentations")
    args = parser.parse_args()

    convert_pptx_to_pdf(
        args.subject_name, Path(args.input)
    )


if __name__ == "__main__":
    main()