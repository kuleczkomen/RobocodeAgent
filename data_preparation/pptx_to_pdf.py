from pathlib import Path
import argparse
import subprocess
import sys


SUBJECT_NAME = "arduino_junior"
INPUT_FOLDER_PATH = Path("../ dataset_pptx")
OUTPUT_FOLDER_PATH = Path(f"../dataset/{SUBJECT_NAME}")


def find_pptx_files(input_folder: Path) -> list[Path]:
    """Find PPTX files in the main folder and one level of subfolders."""
    files = list(input_folder.glob("*.pptx"))

    for subfolder in input_folder.iterdir():
        if subfolder.is_dir():
            files.extend(subfolder.glob("*.pptx"))

    return files


def convert_pptx_to_pdf(input_folder: Path, output_folder: Path) -> None:
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
    args = parser.parse_args()

    convert_pptx_to_pdf(
        INPUT_FOLDER_PATH,
        OUTPUT_FOLDER_PATH,
    )


if __name__ == "__main__":
    main()