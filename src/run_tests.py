import json
import subprocess
import sys
from pathlib import Path

from src.config import GENERATED_TESTS_DIR, REPORTS_DIR
from src.score_tests import score_file


def run_pytest(path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    return {
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def find_generated_tests() -> list[Path]:
    return sorted(
        GENERATED_TESTS_DIR.glob("*/temp_*/test_generated_run_*.py")
    )


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    test_files = find_generated_tests()

    if not test_files:
        print("No generated test files found.")
        print(f"Looked under: {GENERATED_TESTS_DIR}/*/temp_*/test_generated_run_*.py")

    for test_file in test_files:
        print(f"Scoring and running {test_file}")

        score = score_file(test_file)

        if score["syntax_valid"]:
            pytest_result = run_pytest(test_file)
        else:
            pytest_result = {
                "returncode": None,
                "passed": False,
                "stdout": "",
                "stderr": "Skipped pytest because syntax is invalid.",
            }

        results.append({**score, "pytest": pytest_result})

    output_file = REPORTS_DIR / "execution_results.json"
    output_file.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Wrote {output_file}")
    print(f"Processed {len(results)} generated test files.")


if __name__ == "__main__":
    main()