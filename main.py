import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from src.utils.file_io import build_content_block, gather_files

load_dotenv()
model_id = "claude-sonnet-5"

DEFAULT_PROMPT = (
    "This is an image of a medical prescription. Carefully transcribe its "
    "contents and extract the following fields into clearly labeled markdown "
    "sections. If a field is not present or illegible, write 'Not specified' "
    "or 'Illegible' — do not guess or infer missing information.\n\n"
    "1. **Patient Information**: name, age/DOB, sex (if present)\n"
    "2. **Prescriber Information**: doctor name, clinic/hospital, "
    "registration/license number, contact details (if present)\n"
    "3. **Date**: date the prescription was written\n"
    "4. **Medications**: for each medication listed, extract:\n"
    "   - Drug name (as written)\n"
    "   - Strength/dosage (e.g., 500mg)\n"
    "   - Form (tablet, syrup, injection, etc., if stated)\n"
    "   - Frequency/timing (e.g., twice daily, after meals)\n"
    "   - Duration (e.g., for 5 days)\n"
    "   - Quantity prescribed (if stated)\n"
    "5. **Special Instructions**: any additional notes, warnings, or "
    "instructions written by the prescriber\n"
    "6. **Diagnosis/Indication**: if noted on the prescription\n\n"
    "Preserve the exact wording and abbreviations as written on the "
    "prescription (e.g., 'bd', 'od', 'prn', 'tds') rather than expanding or "
    "interpreting them. Do not provide medical advice, dosage validation, "
    "drug interaction checks, or any clinical commentary — this is a "
    "transcription task only."
)


def ocr_file(client: Anthropic, path: Path, prompt: str) -> str:
    content_block = build_content_block(path)
    message = client.messages.create(
        model=model_id,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    content_block,
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Extract prescription data using Claude.")
    parser.add_argument("input", help="Path to an image/PDF file, or a folder of them.")
    parser.add_argument("--out", default=None, help="Write results to this JSON file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    try:
        files = gather_files(input_path)
    except FileNotFoundError as e:
        sys.exit(str(e))

    if not files:
        sys.exit(f"No supported image/PDF files found in {input_path}")

    results = {}
    for f in files:
        print(f"Processing {f.name} …", file=sys.stderr)
        try:
            text = ocr_file(client, f, DEFAULT_PROMPT)
        except Exception as e:
            text = f"[ERROR: {e}]"
        results[str(f)] = text

    if args.out:
        with open(args.out, "w", encoding="utf-8") as out_f:
            json.dump(results, out_f, ensure_ascii=False, indent=2)
        print(f"Wrote results to {args.out}", file=sys.stderr)
    else:
        for path, text in results.items():
            print(f"\n===== {path} =====\n{text}")


if __name__ == "__main__":
    main()
