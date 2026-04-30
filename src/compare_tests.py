import json
from difflib import SequenceMatcher
from pathlib import Path

from src.config import GENERATED_TESTS_DIR, REPORTS_DIR


def similarity(a: str, b: str) -> float:
    return round(SequenceMatcher(None, a, b).ratio(), 4)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(GENERATED_TESTS_DIR.glob("temp_*/test_generated_run_*.py"))
    comparisons = []

    for i, file_a in enumerate(files):
        code_a = file_a.read_text(encoding="utf-8")
        for file_b in files[i + 1:]:
            code_b = file_b.read_text(encoding="utf-8")
            comparisons.append(
                {
                    "file_a": str(file_a.relative_to(GENERATED_TESTS_DIR.parent)),
                    "file_b": str(file_b.relative_to(GENERATED_TESTS_DIR.parent)),
                    "similarity": similarity(code_a, code_b),
                }
            )

    output_file = REPORTS_DIR / "similarity_results.json"
    output_file.write_text(json.dumps(comparisons, indent=2), encoding="utf-8")
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
